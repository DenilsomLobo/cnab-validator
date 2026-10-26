import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


# Usa somente dados inventados e nomes explícitos para impedir confusão com produção.
BANCOS_TESTE = {
    "341": "itau",
    "237": "bradesco",
    "033": "santander",
    "001": "banco_do_brasil",
    "756": "sicoob",
    "104": "caixa",
}


# Preenche posições fixas e rejeita campos que ultrapassem as 400 posições.
def montar_registro(campos, sequencia):

    linha = list(" " * 400)

    for inicio, valor in campos.items():
        if inicio < 1 or inicio + len(valor) - 1 > 394:
            raise ValueError("Campo fora das posições disponíveis")

        linha[inicio - 1:inicio - 1 + len(valor)] = valor

    linha[394:400] = f"{sequencia:06d}"
    return "".join(linha)


# Monta cabeçalhos separados por banco; as contas e inscrições são fictícias.
def montar_cabecalho(codigo, retorno):

    campos = {
        1: "02RETORNO" if retorno else "01REMESSA",
        10: "01",
        12: "COBRANCA".ljust(15),
        27: "1234",
        47: "EMPRESA FICTICIA TESTE LOCAL",
        77: codigo,
        80: BANCOS_TESTE[codigo].upper()[:15].ljust(15),
        95: "261026",
    }

    if codigo == "341":
        campos.update({31: "00", 33: "12345", 38: "6"})

        if retorno:
            campos.update({109: "00001", 114: "261026"})

    elif codigo == "237":
        campos[27] = "0" * 20

        if not retorno:
            campos.update({109: "MX", 111: "0000001"})

    elif codigo == "033":
        campos[27] = "0" * 20

    elif codigo in ("001", "756"):
        campos.update({32: "00012345", 40: "6", 101: "0000001"})

        if codigo == "001":
            campos[130] = "1234567"

    elif codigo == "104":
        campos[31] = "0001234"

    return montar_registro(campos, 1)


# Usa posições próprias de cada banco para os campos de identificação do detalhe.
def montar_detalhe(codigo, retorno, numero, valor):

    campos = {
        1: "7" if codigo == "001" else "1",
        2: "02",
        4: "0" * 14,
        109: "06" if retorno else "01",
    }

    if codigo == "341":
        campos.update({18: "1234", 22: "00", 24: "12345", 29: "6",
                       63: f"{numero:08d}"})

    elif codigo == "237":
        campos.update({21: "0" * 17, 71: f"{numero:011d}", 82: "0"})

    elif codigo == "033":
        campos.update({18: "1234", 22: "00012345", 30: "00012345", 63: f"{numero:08d}"})

    elif codigo == "001":
        campos.update({18: "1234", 23: "00012345", 32: "1234567",
                       64: f"{numero:017d}", 107: "17"})

    elif codigo == "756":
        campos.update({18: "1234", 22: "0", 23: "00012345", 31: "6",
                       63: f"{numero:011d}", 74: "0", 107: "01"})

    elif codigo == "104":
        campos.update({21: "0001234", 57: "14", 59: f"{numero:015d}", 107: "01"})

    # Valores de retorno e datas de crédito não usam as posições da remessa.
    if retorno:
        campos.update({111: "261026", 147: "271026", 153: f"{valor:013d}"})

        for inicio in (176, 215, 228, 241, 254, 267, 280):
            campos[inicio] = "0" * 13

        campos[254] = f"{valor:013d}"
        campos[176 if codigo == "756" else 296] = "271026"

        if codigo == "341":
            campos[83] = "109"

    else:
        campos.update({
            111: f"TESTE{numero:05d}", 121: "271026", 127: f"{valor:013d}",
            140: codigo, 143: "00000", 150: "N", 151: "261026",
            161: "0" * 13, 174: "000000", 180: "0" * 13, 193: "0" * 13,
            206: "0" * 13, 219: "02", 221: "0" * 14,
            235: f"PAGADOR FICTICIO {numero}", 275: "RUA DE TESTE SEM VALIDADE",
            327: "01001000", 335: "SAO PAULO", 350: "SP",
        })

        if codigo == "341":
            campos.update({71: "0" * 13, 84: "109"})

        if codigo == "237":
            campos[140] = "000"

        if codigo == "756":
            campos.update({150: "0", 173: "2", 193: "9" + "0" * 12})

    return montar_registro(campos, numero + 1)


# Preenche os totais somente nas posições conhecidas do perfil de teste.
def montar_trailer(codigo, retorno, quantidade, total):

    campos = {1: "9"}

    if codigo == "341" and retorno:
        campos.update({1: "9201341", 18: "0" * 22, 58: "0" * 22,
                       178: "0" * 22, 208: "00001", 213: f"{quantidade:08d}",
                       221: f"{total:014d}"})

    if codigo == "033" and not retorno:
        campos.update({2: f"{quantidade + 2:06d}", 8: f"{total:013d}", 21: "0" * 374})

    if codigo == "756" and retorno:
        campos.update({2: "02", 4: "756", 156: "26102026", 164: f"{quantidade:08d}"})

    return montar_registro(campos, quantidade + 2)


# Cria três títulos por arquivo, permitindo testar também a prévia de cinco linhas.
def montar_arquivo(codigo, retorno=False):

    valores = [12500, 25000, 8750]
    linhas = [montar_cabecalho(codigo, retorno)]

    for numero, valor in enumerate(valores, 1):
        linhas.append(montar_detalhe(codigo, retorno, numero, valor))

    linhas.append(montar_trailer(codigo, retorno, len(valores), sum(valores)))
    return linhas


# Guarda o caso e as expectativas para os testes e o guia de uso manual.
def adicionar_caso(casos, nome, codigo, linhas, campos_erros=None):

    campos_erros = campos_erros or []
    casos.append({
        "arquivo": nome, "banco": codigo, "linhas": linhas,
        "situacao": "Inválido" if campos_erros else "Validação incompleta",
        "campos_erros": campos_erros,
    })


# Produz casos sem erros nas regras atuais e casos que devem falhar por uma causa conhecida.
def criar_casos():

    casos = []

    for codigo, nome in BANCOS_TESTE.items():
        remessa = montar_arquivo(codigo)
        adicionar_caso(casos, f"{nome}_remessa_base.rem", codigo, remessa)

        # O retorno BB não é inventado: seu mapa CBR643 ainda não foi implementado.
        if codigo != "001":
            adicionar_caso(casos, f"{nome}_retorno_base.ret", codigo, montar_arquivo(codigo, True))

        linhas = remessa.copy()
        linhas[1] = linhas[1][:120] + "321326" + linhas[1][126:]
        adicionar_caso(casos, f"{nome}_erro_data.rem", codigo, linhas, ["vencimento"])

        linhas = remessa.copy()
        linhas[1] = linhas[1][:394] + "000099"
        adicionar_caso(casos, f"{nome}_erro_sequencia.rem", codigo, linhas, ["sequencia"])

        linhas = remessa.copy()
        linhas[1] = linhas[1][:120]
        adicionar_caso(casos, f"{nome}_erro_truncado.rem", codigo, linhas, ["registro"])

        adicionar_caso(casos, f"{nome}_sem_trailer.rem", codigo, remessa[:-1], ["trailer"])

    # Inclui divergências de total para os bancos que já conferem esses campos.
    linhas = montar_arquivo("033")
    linhas[-1] = linhas[-1][:7] + "0000000000001" + linhas[-1][20:]
    adicionar_caso(casos, "santander_erro_total.rem", "033", linhas, ["valor_total"])

    linhas = montar_arquivo("341", True)
    linhas[-1] = linhas[-1][:220] + "00000000000001" + linhas[-1][234:]
    adicionar_caso(casos, "itau_erro_total.ret", "341", linhas, ["valor_total"])

    linhas = montar_arquivo("756", True)
    linhas[-1] = linhas[-1][:163] + "00000099" + linhas[-1][171:]
    adicionar_caso(casos, "sicoob_erro_quantidade.ret", "756", linhas, ["quantidade_detalhes"])

    adicionar_caso(casos, "arquivo_vazio.txt", "", [], ["arquivo"])
    return casos


# Escreve em ASCII e CRLF para manter os bytes e espaços de cada registro.
def salvar_casos(pasta):

    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    manifesto = []

    for caso in criar_casos():
        texto = "\r\n".join(caso["linhas"])

        if caso["linhas"]:
            texto += "\r\n"

        (pasta / caso["arquivo"]).write_bytes(texto.encode("ascii"))
        manifesto.append({chave: valor for chave, valor in caso.items() if chave != "linhas"})

    (pasta / "resultados_esperados.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=4), encoding="utf-8",
    )

    return manifesto


# Gera os arquivos e um ZIP contendo somente os exemplos e o guia da pasta.
def main():

    pasta = Path(__file__).resolve().parent / "bancos"
    manifesto = salvar_casos(pasta)
    caminho_zip = pasta.parent / "cnab_testes.zip"

    with ZipFile(caminho_zip, "w", ZIP_DEFLATED) as pacote:
        for item in manifesto:
            pacote.write(pasta / item["arquivo"], item["arquivo"])

        pacote.write(pasta / "resultados_esperados.json", "resultados_esperados.json")

        if (pasta / "LEIA-ME.md").exists():
            pacote.write(pasta / "LEIA-ME.md", "LEIA-ME.md")

    print(f"Gerados {len(manifesto)} arquivos em {pasta}")
    print(f"Pacote: {caminho_zip}")


# Permite importar o gerador nos testes sem gravar arquivos automaticamente.
if __name__ == "__main__":
    main()
