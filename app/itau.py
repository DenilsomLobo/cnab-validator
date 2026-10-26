"""Itaú cobrança CNAB 400, manual janeiro/2017, páginas 7–18.

Regras de campos principais e estrutura. Condições contratuais e variantes
não cobertas geram alertas explícitos, sem alegação de homologação bancária.
"""
from app.validator import validar_data, validar_numerico

MANUAL = "https://download.itau.com.br/bankline/layout_cobranca_400bytes_cnab_itau.pdf"
TIPOS = {"0": "Cabeçalho", "1": "Detalhe", "2": "Multa", "4": "Rateio",
         "5": "Complemento", "9": "Trailer"}


# Identifica o perfil Itaú pelas posições do cabeçalho, e não pelo nome do arquivo.
def identificar(linhas):
    header = linhas[0] if linhas else ""
    banco = header[76:79] if header.startswith("0") else ""
    servico = header[9:11] if header.startswith("0") else ""
    operacao = header[1:2] if header.startswith("0") else ""
    return {
        "banco": "Itaú (341)" if banco == "341" else banco or "Não identificado",
        "servico": "Cobrança" if servico == "01" else servico or "Não identificado",
        "operacao": {"1": "Remessa", "2": "Retorno"}.get(operacao, "Não identificada"),
        "suportado": banco == "341" and servico == "01" and operacao in ("1", "2"),
    }


# Percorre os registros e aplica regras de estrutura, campos e totais Itaú.
def analisar_itau(linhas):
    info = identificar(linhas)
    erros, alertas, registros = [], [], []
    total = 0
    total_completo = True
    detalhes = 0

    # Centraliza a criação das mensagens para separar erros de alertas.
    def adicionar(n, campo, valor, motivo, classificacao="ERRO"):
        item = dict(linha=n, campo=campo, valor=str(valor),
                    classificacao=classificacao, motivo=motivo)
        (erros if classificacao == "ERRO" else alertas).append(item)

    if not linhas:
        adicionar(0, "arquivo", "", "Arquivo vazio")
    elif not info["suportado"]:
        adicionar(1, "cabecalho", linhas[0][:79],
                  "Cabeçalho não identifica Itaú cobrança remessa/retorno. Perfil não aplicado.")

    if linhas and info["suportado"]:
        retorno = info["operacao"] == "Retorno"
        permitidos = "0149" if retorno else "012459"
        if sum(l.startswith("0") for l in linhas) != 1:
            adicionar(1, "cabecalho", "", "Deve existir exatamente um cabeçalho, na primeira linha")
        if not linhas[-1].startswith("9"):
            adicionar(len(linhas), "trailer", "", "Trailer ausente no final do arquivo")
        if sum(l.startswith("9") for l in linhas) != 1:
            adicionar(len(linhas), "trailer", "", "Deve existir exatamente um trailer")
        ultimo_detalhe = False
        complementos = set()
        for n, linha in enumerate(linhas, 1):
            tipo = linha[:1]
            registros.append({"Linha": n, "Tipo": TIPOS.get(tipo, "Desconhecido"),
                              "Caracteres": len(linha), "Sequência": linha[394:400]})
            if len(linha) != 400:
                adicionar(n, "registro", len(linha), "Registro truncado" if len(linha) < 400
                          else "Registro excede 400 posições")
                total_completo = False
                ultimo_detalhe = False
                continue
            if not linha.isascii():
                adicionar(n, "codificacao", "", "Caracteres fora de ASCII; conferir exportação", "ALERTA")

            # Extrai o campo usando as posições inclusivas indicadas pelo manual.
            def campo(nome, inicio, fim, regra="numero", esperado=None, opcional=False):
                valor = linha[inicio - 1:fim]
                if regra == "numero":
                    ok = validar_numerico(valor)
                elif regra == "data":
                    ok = (opcional and valor == "0" * len(valor)) or validar_data(valor)
                elif regra == "fixo":
                    ok = valor == esperado
                else:
                    ok = bool(valor.strip())
                if not ok:
                    adicionar(n, nome, valor, f"Campo inválido nas posições {inicio}–{fim}")
                    erros[-1].update({
                        "inicio": inicio, "fim": fim,
                        "esperado": repr(esperado) if regra == "fixo" else regra,
                        "referencia": MANUAL,
                    })
                return valor

            sequencia = campo("sequencia", 395, 400)
            if validar_numerico(sequencia) and int(sequencia) != n:
                adicionar(n, "sequencia", sequencia, f"Sequência esperada: {n:06d}")
            if tipo not in permitidos:
                adicionar(n, "tipo", tipo, "Tipo não previsto neste perfil")
                total_completo = False
            elif tipo == "0":
                if n != 1:
                    adicionar(n, "cabecalho", tipo, "Cabeçalho fora da primeira linha")
                campo("movimento", 3, 9, "fixo", "RETORNO" if retorno else "REMESSA")
                campo("servico", 12, 26, "fixo", "COBRANCA".ljust(15))
                for nome, a, b in [("agencia",27,30),("conta",33,37),("dac",38,38)]:
                    campo(nome, a, b)
                campo("zeros", 31, 32, "fixo", "00")
                campo("data_geracao", 95, 100, "data")
                if retorno:
                    campo("controle_arquivo", 109, 113)
                    campo("data_credito",114,119,"data",opcional=True)
                ultimo_detalhe = False
            elif tipo == "9":
                if n != len(linhas):
                    adicionar(n, "trailer", tipo, "Há registros após o trailer")
                if not retorno:
                    campo("reservado", 2, 394, "fixo", " " * 393)
                else:
                    campo("operacao", 2, 2, "fixo", "2")
                    campo("servico", 3, 4, "fixo", "01")
                    campo("banco", 5, 7, "fixo", "341")
                    controle = campo("controle_arquivo", 208, 212)
                    if controle != linhas[0][108:113]:
                        adicionar(n, "controle_arquivo", controle, "Controle difere do cabeçalho")
                    quantidade = campo("quantidade_detalhes", 213, 220)
                    valor_total = campo("valor_total", 221, 234)
                    # Os saldos de carteira da nota 21 não são totais deste arquivo.
                    for nome,a,b in [("saldo_simples_quantidade",18,25),("saldo_simples_valor",26,39),
                                     ("saldo_vinculada_quantidade",58,65),("saldo_vinculada_valor",66,79),
                                     ("saldo_escritural_quantidade",178,185),("saldo_escritural_valor",186,199)]:
                        campo(nome,a,b)
                    if total_completo:
                        if validar_numerico(quantidade) and int(quantidade) != detalhes:
                            adicionar(n, "quantidade_detalhes", quantidade, f"Esperado: {detalhes}")
                        if validar_numerico(valor_total) and int(valor_total) != total:
                            adicionar(n, "valor_total", valor_total, f"Esperado em centavos: {total}")
                    else:
                        adicionar(n, "totais", "", "Conferência dos totais indisponível por registros incompletos ou variantes", "ALERTA")
                ultimo_detalhe = False
            elif tipo == "1":
                detalhes += 1
                ultimo_detalhe = True
                complementos = set()
                for nome, a, b in [("inscricao",4,17),("agencia",18,21),("conta",24,28),
                                    ("dac",29,29),("nosso_numero",63,70),("ocorrencia",109,110)]:
                    campo(nome,a,b)
                campo("zeros",22,23,"fixo","00")
                inscricao = campo("tipo_inscricao",2,3)
                if inscricao not in (("01","02") if retorno else ("01","02","03","04")):
                    adicionar(n,"tipo_inscricao",inscricao,"Tipo de inscrição não previsto")
                if retorno and linha[108:110] in ("69", "76"):
                    total_completo = False
                    adicionar(n, "variante", linha[108:110], "Cheque devolvido: campos específicos ainda não validados", "ALERTA")
                    continue
                carteira = campo("carteira",83 if retorno else 84,85 if retorno else 86)
                if retorno:
                    campo("data_ocorrencia",111,116,"data")
                    campo("vencimento",147,152,"data",opcional=True)
                    valor = campo("valor",153,165)
                    for nome,a,b in [("tarifa",176,188),("iof",215,227),("abatimento",228,240),
                                     ("desconto",241,253),("principal",254,266),("juros",267,279),
                                     ("outros_creditos",280,292)]:
                        campo(nome,a,b)
                    campo("data_credito",296,301,"data",opcional=True)
                else:
                    entrada = linha[108:110] == "01"
                    campo("vencimento",121,126,"data",opcional=not entrada and linha[108:110] not in ("06","37"))
                    valor = campo("valor",127,139)
                    if entrada:
                        campo("banco",140,142,"fixo","341")
                        campo("agencia_cobradora",143,147,"fixo","00000")
                        campo("emissao",151,156,"data")
                        campo("nome_pagador",235,264,"texto")
                        campo("endereco_pagador",275,314,"texto")
                        campo("cidade_pagador",335,349,"texto")
                        campo("cep",327,334)
                        for nome,a,b in [("moeda",71,83),("juros",161,173),("desconto",180,192),
                                         ("iof",193,205),("abatimento",206,218),("inscricao_pagador",221,234)]:
                            campo(nome,a,b)
                        campo("data_desconto",174,179,"data",opcional=True)
                        if linha[149] not in "AN":
                            adicionar(n,"aceite",linha[149],"Aceite deve ser A ou N")
                        if linha[218:220] not in ("01","02"):
                            adicionar(n,"tipo_inscricao_pagador",linha[218:220],"Utilize 01 para CPF ou 02 para CNPJ")
                        if validar_numerico(valor) and int(valor) == 0:
                            adicionar(n,"valor",valor,"Título de entrada deve ter valor positivo")
                    else:
                        adicionar(n,"ocorrencia",linha[108:110],"Comando: condições específicas da ocorrência ainda não cobertas", "ALERTA")
                if validar_numerico(valor):
                    total += int(valor)
                else:
                    total_completo = False
                if carteira not in ("109", "112", "115", "121", "180"):
                    adicionar(n,"carteira",carteira,"Condições específicas desta carteira não cobertas", "ALERTA")
            else:
                if not ultimo_detalhe:
                    adicionar(n, "ordem", tipo, "Complemento sem detalhe anterior")
                if tipo in ("2", "5") and tipo in complementos:
                    adicionar(n,"ordem",tipo,"Complemento duplicado para o mesmo título")
                complementos.add(tipo)
                if tipo == "2":
                    codigo = linha[1]
                    if codigo not in "012":
                        adicionar(n,"codigo_multa",codigo,"Código de multa deve ser 0, 1 ou 2")
                    data = linha[2:10]
                    if codigo != "0":
                        from datetime import datetime
                        try:
                            if not validar_numerico(data):
                                raise ValueError
                            datetime.strptime(data,"%d%m%Y")
                        except ValueError:
                            adicionar(n,"data_multa",data,"Data de multa deve ser DDMMAAAA válida")
                    campo("multa",11,23)
                    campo("reservado",24,394,"fixo"," " * 371)
                else:
                    adicionar(n, "cobertura", tipo, "Complemento reconhecido; campos específicos ainda não validados", "ALERTA")
                if retorno:
                    total_completo = False
        if not detalhes:
            adicionar(1, "detalhes", "0", "Arquivo sem registro de detalhe")
    invalidos = {e["linha"] for e in erros if e["linha"] > 0}
    return {"validos": len(linhas) - len(invalidos) if info["suportado"] else 0,
            "invalidos": len(invalidos),
            "erros": erros, "alertas": alertas, "identificacao": info,
            "registros": registros, "total_centavos": total,
            "detalhes": detalhes, "total_completo": total_completo}
