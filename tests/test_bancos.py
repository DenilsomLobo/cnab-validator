import csv
from io import StringIO

import pytest

from app.bancos import analisar_bancario, identificar_banco
from app.layouts import BANCOS, CAMPOS_REMESSA, CAMPOS_RETORNO
from app.report import gerar_csv, gerar_relatorio


# Monta registros sintéticos com posições explícitas para os testes de estrutura.
def montar_registro(campos, sequencia):

    registro = list(" " * 400)

    for inicio, valor in campos.items():
        registro[inicio - 1:inicio - 1 + len(valor)] = valor

    registro[394:400] = f"{sequencia:06d}"
    return "".join(registro)


# Cria um arquivo pequeno para exercitar o perfil de cada banco sem dados reais.
def montar_arquivo(codigo, retorno=False):

    movimento = "retorno" if retorno else "remessa"
    cabecalho = montar_registro({
        1: "02RETORNO" if retorno else "01REMESSA",
        10: "01", 12: "COBRANCA".ljust(15), 77: codigo, 95: "261026",
        130: "1234567",
    }, 1)

    campos = {1: BANCOS[codigo]["detalhe_" + movimento]}
    mapa = CAMPOS_RETORNO[codigo] if retorno else CAMPOS_REMESSA[codigo]

    for nome, inicio, fim, regra in mapa:
        campos[inicio] = "0" * (fim - inicio + 1)

    campos[109] = "06" if retorno else "01"

    if retorno:
        campos.update({111: "261026", 147: "271026", 153: "0000000012500"})
        campos[176 if codigo == "756" else 296] = "271026"
    else:
        campos.update({121: "271026", 127: "0000000012500", 151: "261026",
                       235: "PAGADOR", 327: "01001000"})

    trailer = {1: "9"}

    if codigo == "033" and not retorno:
        trailer.update({2: "000003", 8: "0000000012500"})

    if codigo == "756" and retorno:
        trailer[164] = "00000001"

    return [cabecalho, montar_registro(campos, 2), montar_registro(trailer, 3)]


# Verifica todos os novos perfis e garante que cobertura parcial não vire aprovação.
@pytest.mark.parametrize("codigo", ["237", "033", "001", "756", "104"])
@pytest.mark.parametrize("retorno", [False, True])
def test_perfis_e_cobertura(codigo, retorno):

    if codigo == "001" and retorno:
        resultado = analisar_bancario([montar_registro({1: "02RETORNO", 10: "01", 77: codigo}, 1)])
        assert resultado["situacao"] == "Validação incompleta"
        assert resultado["validos"] == 0
        return

    resultado = analisar_bancario(montar_arquivo(codigo, retorno))
    assert resultado["erros"] == []
    assert resultado["incompletos"] == 1
    assert resultado["validos"] == 2
    assert resultado["total_centavos"] == 12500
    assert resultado["situacao"] == "Validação incompleta"


# Confirma que campos do banco errado nunca são aplicados ao conteúdo recebido.
def test_banco_divergente_e_desconhecido():

    resultado = analisar_bancario(montar_arquivo("237"), "033")
    assert not resultado["identificacao"]["suportado"]
    assert resultado["validos"] == 0
    assert resultado["invalidos"] == 1
    assert resultado["incompletos"] == 2

    resultado = analisar_bancario(["X" * 400])
    assert resultado["validos"] == 0
    assert resultado["situacao"] == "Validação incompleta"


# Exercita campos inválidos e exige posição, formato esperado e fonte no relatório.
@pytest.mark.parametrize("codigo", ["237", "033", "001", "756", "104"])
def test_data_invalida_com_diagnostico(codigo):

    linhas = montar_arquivo(codigo)
    linhas[1] = linhas[1][:120] + "321326" + linhas[1][126:]
    resultado = analisar_bancario(linhas)
    erro = next(item for item in resultado["erros"] if item["campo"] == "vencimento")
    assert erro["inicio"] == 121
    assert erro["fim"] == 126
    assert "DDMMAA" in erro["esperado"]
    assert erro["referencia"].startswith("https://")
    assert resultado["invalidos"] == 1
    assert resultado["incompletos"] == 0


# Garante que sequência incorreta, cabeçalho duplicado e trailer fora de ordem falhem.
def test_estrutura_e_sequencia():

    linhas = montar_arquivo("237")
    linhas[1] = linhas[1][:394] + "000008"
    assert any(item["campo"] == "sequencia" for item in analisar_bancario(linhas)["erros"])

    linhas = montar_arquivo("237")
    linhas.insert(1, linhas[0])
    assert any(item["campo"] == "cabecalho" for item in analisar_bancario(linhas)["erros"])

    linhas = montar_arquivo("237")
    linhas.append(linhas[1])
    assert any(item["campo"] == "trailer" for item in analisar_bancario(linhas)["erros"])


# Confere totais em posições próprias de cada banco e suspende somas incompletas.
def test_totais_e_truncamento():

    linhas = montar_arquivo("033")
    linhas[-1] = montar_registro({1: "9", 2: "000004", 8: "0000000012501"}, 3)
    campos = {item["campo"] for item in analisar_bancario(linhas)["erros"]}
    assert "quantidade_registros" in campos
    assert "valor_total" in campos

    linhas[1] = linhas[1][:100]
    resultado = analisar_bancario(linhas)
    assert not resultado["total_completo"]
    assert not any(item["campo"] == "valor_total" for item in resultado["erros"])

    linhas = montar_arquivo("756", True)
    linhas[-1] = montar_registro({1: "9", 164: "00000002"}, 3)
    assert any(item["campo"] == "quantidade_detalhes" for item in analisar_bancario(linhas)["erros"])


# Testa o formato legado Santander e a identificação de CNAB 240 sem aplicar mapa 400.
def test_identificacao_legada_e_240():

    linhas = montar_arquivo("033")
    linhas[0] = linhas[0][:76] + "353" + linhas[0][79:]
    assert identificar_banco(linhas)["codigo"] == "033"
    assert identificar_banco(["75600000".ljust(240)])["formato"] == "CNAB 240"
    assert not identificar_banco(["75600000".ljust(240)])["suportado"]


# Valida exportação de acentos, metadados, fórmulas e preservação de relatórios anteriores.
def test_csv_e_relatorios(tmp_path, monkeypatch):

    itens = [{"linha": 1, "campo": "=COMANDO", "valor": "@DADO", "motivo": "+TEXTO",
              "classificacao": "ALERTA", "inicio": 2, "fim": 3, "esperado": "DDMMAA"}]
    dados = gerar_csv(itens)
    registro = next(csv.DictReader(StringIO(dados.decode("utf-8-sig")), delimiter=";"))
    assert registro["valor"] == "'@DADO"
    assert registro["campo"] == "'=COMANDO"
    assert registro["inicio"] == "2"
    monkeypatch.chdir(tmp_path)
    primeiro = gerar_relatorio(itens)
    segundo = gerar_relatorio(itens)
    assert primeiro != segundo
    assert primeiro.read_bytes() == dados
