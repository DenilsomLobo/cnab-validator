# Importa os mapas dos bancos e as funções que já fazem parte do projeto.
from app.itau import analisar_itau
from app.layouts import BANCOS, CAMPOS_REMESSA, CAMPOS_RETORNO
from app.resultados import classificar_resultado
from app.validator import validar_data, validar_numerico


# Lê a identificação pelo conteúdo, sem depender da extensão ou do nome do arquivo.
def identificar_banco(linhas):

    cabecalho = linhas[0] if linhas else ""
    codigo = cabecalho[76:79]

    # O Santander também possui arquivos do padrão legado identificado por 353.
    if codigo == "353":
        codigo = "033"

    banco = BANCOS.get(codigo)
    operacao = {"1": "Remessa", "2": "Retorno"}.get(cabecalho[1:2], "Não identificada")
    servico = cabecalho[9:11]
    formato = "CNAB 400"

    # Reconhece um cabeçalho de 240 posições, mas não aplica o mapa de 400 a ele.
    if len(cabecalho) == 240 and cabecalho[3:8] == "00000":
        codigo = cabecalho[:3]
        banco = BANCOS.get(codigo)
        formato = "CNAB 240"

    suportado = (
        banco is not None
        and formato == "CNAB 400"
        and cabecalho.startswith("0")
        and servico == "01"
        and operacao in ("Remessa", "Retorno")
    )

    # O manual BB consultado cobre CBR641; o CBR643 precisa de seu mapa próprio.
    if codigo == "001" and operacao == "Retorno":
        suportado = False

    return {
        "codigo": codigo,
        "banco": banco["nome"] if banco else "Não identificado",
        "servico": "Cobrança" if servico == "01" and formato == "CNAB 400" else "Não identificado",
        "operacao": operacao,
        "formato": formato,
        "suportado": suportado,
        "versao": banco["versao"] if banco else "Não identificada",
        "manual": banco["manual"] if banco else "",
    }


# Registra posições, formato esperado e manual junto da mensagem de cada ocorrência.
def adicionar_ocorrencia(resultado, numero, campo, valor, motivo,
                         inicio=0, fim=0, esperado="", classificacao="ERRO"):

    ocorrencia = {
        "linha": numero,
        "campo": campo,
        "valor": str(valor),
        "classificacao": classificacao,
        "motivo": motivo,
        "inicio": inicio,
        "fim": fim,
        "esperado": esperado,
        "referencia": resultado["identificacao"]["manual"],
    }

    if classificacao == "ERRO":
        resultado["erros"].append(ocorrencia)
    else:
        resultado["alertas"].append(ocorrencia)


# Extrai o campo e verifica sua regra usando posições inclusivas do manual.
def conferir_campo(resultado, linha, numero, nome, inicio, fim, regra, esperado=None):

    valor = linha[inicio - 1:fim]
    descricao = regra

    if regra == "numero":
        correto = validar_numerico(valor)
        descricao = f"{fim - inicio + 1} dígitos ASCII"
    elif regra == "data":
        correto = validar_data(valor)
        descricao = "Data válida no formato DDMMAA"
    elif regra == "data_opcional":
        correto = valor == "000000" or validar_data(valor)
        descricao = "DDMMAA ou 000000 quando não aplicável"
    elif regra == "fixo":
        correto = valor == esperado
        descricao = repr(esperado)
    else:
        correto = bool(valor.strip())
        descricao = "Texto preenchido"

    if not correto:
        adicionar_ocorrencia(resultado, numero, nome, valor, "Conteúdo fora do formato esperado",
                             inicio, fim, descricao)

    return valor


# Analisa os bancos por um fluxo comum e usa os campos específicos de cada perfil.
def analisar_bancario(linhas, banco_esperado=None):

    info = identificar_banco(linhas)
    resultado = {
        "identificacao": info, "erros": [], "alertas": [], "registros": [],
        "detalhes": 0, "total_centavos": 0, "total_completo": True,
    }

    if not linhas:
        adicionar_ocorrencia(resultado, 0, "arquivo", "", "Arquivo vazio")
        return classificar_resultado(resultado, linhas)

    # Interrompe a seleção de regras se o banco escolhido divergir do cabeçalho.
    if banco_esperado and banco_esperado != info["codigo"]:
        info["suportado"] = False
        adicionar_ocorrencia(resultado, 1, "banco", info["codigo"],
                             "O banco escolhido difere do conteúdo do arquivo", 77, 79, banco_esperado)

    if not info["suportado"]:
        adicionar_ocorrencia(resultado, 0, "perfil", info["formato"],
                             "Perfil sem mapa aplicável. Nenhum campo bancário foi validado.",
                             classificacao="ALERTA")
        return classificar_resultado(resultado, linhas)

    # Preserva o motor Itaú existente e acrescenta a classificação de cobertura.
    if info["codigo"] == "341":
        resultado = analisar_itau(linhas)
        resultado["identificacao"] = info

        for item in resultado["erros"] + resultado["alertas"]:
            item.setdefault("inicio", 0)
            item.setdefault("fim", 0)
            item.setdefault("esperado", "Consultar regra no manual")
            item["referencia"] = info["manual"]

        for numero, linha in enumerate(linhas, 1):
            if linha.startswith("1"):
                adicionar_ocorrencia(resultado, numero, "cobertura", "",
                                     "Campos principais verificados; regras de carteira, comandos e DAC ainda parciais.",
                                     classificacao="ALERTA")

        return classificar_resultado(resultado, linhas)

    banco = BANCOS[info["codigo"]]
    retorno = info["operacao"] == "Retorno"
    movimento = "retorno" if retorno else "remessa"
    tipo_detalhe = banco["detalhe_" + movimento]
    tipos_permitidos = banco["tipos_" + movimento]
    ultimo_detalhe = False

    # Verifica a existência e a posição dos registros que abrem e fecham o arquivo.
    if sum(linha.startswith("0") for linha in linhas) != 1:
        adicionar_ocorrencia(resultado, 1, "cabecalho", "", "Deve existir um único cabeçalho no início")

    if sum(linha.startswith("9") for linha in linhas) != 1 or not linhas[-1].startswith("9"):
        adicionar_ocorrencia(resultado, len(linhas), "trailer", "", "Deve existir um único trailer no final")

    # Percorre todas as linhas, preservando registros vazios e espaços do arquivo.
    for numero, linha in enumerate(linhas, 1):
        tipo = linha[:1]
        nome_tipo = "Detalhe" if tipo == tipo_detalhe else {"0": "Cabeçalho", "9": "Trailer"}.get(tipo, "Complemento")
        resultado["registros"].append({
            "Linha": numero, "Tipo": nome_tipo, "Caracteres": len(linha), "Sequência": linha[394:400],
        })

        if len(linha) != 400:
            adicionar_ocorrencia(resultado, numero, "registro", len(linha),
                                 "Registro truncado" if len(linha) < 400 else "Registro longo",
                                 1, 400, "400 posições")
            resultado["total_completo"] = False
            ultimo_detalhe = False
            continue

        # Caracteres multibyte podem mudar as posições em bytes exigidas pelo banco.
        if not linha.isascii():
            adicionar_ocorrencia(resultado, numero, "codificacao", "",
                                 "Caracteres fora de ASCII: confirme a exportação ANSI do banco.",
                                 classificacao="ALERTA")

        # Compara a sequência de cada linha com sua posição física no arquivo.
        sequencia = conferir_campo(resultado, linha, numero, "sequencia", 395, 400, "numero")

        if validar_numerico(sequencia) and int(sequencia) != numero:
            adicionar_ocorrencia(resultado, numero, "sequencia", sequencia,
                                 "Sequência fora de ordem", 395, 400, f"{numero:06d}")

        if tipo not in tipos_permitidos:
            adicionar_ocorrencia(resultado, numero, "tipo", tipo,
                                 "Tipo não previsto neste perfil", 1, 1, tipos_permitidos)
            resultado["total_completo"] = False
            ultimo_detalhe = False
            continue

        if tipo == "0":
            ultimo_detalhe = False

            if numero != 1:
                adicionar_ocorrencia(resultado, numero, "ordem", tipo, "Cabeçalho fora do início")

            conferir_campo(resultado, linha, numero, "movimento", 3, 9, "fixo", info["operacao"].upper())
            conferir_campo(resultado, linha, numero, "data_geracao", 95, 100, "data")
            literal = linha[11:26].strip()

            if literal not in ("COBRANCA", "COBRANÇA"):
                adicionar_ocorrencia(resultado, numero, "servico", literal,
                                     "Literal de serviço incompatível", 12, 26, "COBRANCA")

            if info["codigo"] == "001":
                convenio = conferir_campo(resultado, linha, numero, "convenio", 130, 136, "numero")

                if validar_numerico(convenio) and int(convenio) <= 1000000:
                    adicionar_ocorrencia(resultado, 0, "versao", convenio,
                                         "Este perfil BB exige convênio acima de 1.000.000", classificacao="ALERTA")

        elif tipo == "9":
            ultimo_detalhe = False

            if numero != len(linhas):
                adicionar_ocorrencia(resultado, numero, "ordem", tipo, "Há registros após o trailer")

        elif tipo == tipo_detalhe:
            ultimo_detalhe = True
            resultado["detalhes"] += 1
            campos = CAMPOS_RETORNO[info["codigo"]] if retorno else CAMPOS_REMESSA[info["codigo"]]

            for nome, inicio, fim, regra in campos:
                conferir_campo(resultado, linha, numero, nome, inicio, fim, regra)

            # Datas e valores de retorno têm posições diferentes da remessa.
            if retorno:
                conferir_campo(resultado, linha, numero, "ocorrencia", 109, 110, "numero")
                conferir_campo(resultado, linha, numero, "data_ocorrencia", 111, 116, "data")
                conferir_campo(resultado, linha, numero, "vencimento", 147, 152, "data_opcional")
                valor = conferir_campo(resultado, linha, numero, "valor", 153, 165, "numero")
                inicio_credito = 176 if info["codigo"] == "756" else 296
                conferir_campo(resultado, linha, numero, "data_credito", inicio_credito, inicio_credito + 5, "data_opcional")
            else:
                entrada = linha[108:110] == "01"
                valor = conferir_campo(resultado, linha, numero, "valor", 127, 139, "numero")

                if entrada:
                    # O layout Sicoob publicado admite 888888 como vencimento à vista.
                    if not (info["codigo"] == "756" and linha[120:126] == "888888"):
                        conferir_campo(resultado, linha, numero, "vencimento", 121, 126, "data")

                    conferir_campo(resultado, linha, numero, "emissao", 151, 156, "data")
                    conferir_campo(resultado, linha, numero, "nome_pagador", 235, 264, "texto")
                    conferir_campo(resultado, linha, numero, "cep", 327, 334, "numero")

            # Soma valores como inteiros em centavos, evitando arredondamento de float.
            if validar_numerico(valor):
                resultado["total_centavos"] += int(valor)
            else:
                resultado["total_completo"] = False

            adicionar_ocorrencia(resultado, numero, "cobertura", "",
                                 "Campos principais verificados; regras condicionais e dígitos verificadores ainda parciais.",
                                 classificacao="ALERTA")

        else:
            # Complementos pertencem ao último detalhe; nunca podem abrir um arquivo.
            if not ultimo_detalhe:
                adicionar_ocorrencia(resultado, numero, "ordem", tipo, "Complemento sem detalhe anterior")

            adicionar_ocorrencia(resultado, numero, "cobertura", tipo,
                                 "Registro complementar reconhecido; campos específicos ainda não cobertos.",
                                 classificacao="ALERTA")

    if not resultado["detalhes"]:
        adicionar_ocorrencia(resultado, 1, "detalhes", "0", "Arquivo sem detalhes")

    # Confere totais somente onde o manual define um total do arquivo, não saldo em carteira.
    conferir_totais(resultado, linhas)

    return classificar_resultado(resultado, linhas)


# Usa posições diferentes para os totais Santander e Sicoob; os demais não são presumidos.
def conferir_totais(resultado, linhas):

    info = resultado["identificacao"]
    trailer = linhas[-1]
    numero = len(linhas)

    if len(trailer) != 400 or not trailer.startswith("9"):
        return

    if info["codigo"] == "033" and info["operacao"] == "Remessa":
        quantidade = conferir_campo(resultado, trailer, numero, "quantidade_registros", 2, 7, "numero")
        total = conferir_campo(resultado, trailer, numero, "valor_total", 8, 20, "numero")

        if validar_numerico(quantidade) and int(quantidade) != len(linhas):
            adicionar_ocorrencia(resultado, numero, "quantidade_registros", quantidade,
                                 "Quantidade difere do arquivo", 2, 7, str(len(linhas)))

        if resultado["total_completo"] and validar_numerico(total) and int(total) != resultado["total_centavos"]:
            adicionar_ocorrencia(resultado, numero, "valor_total", total,
                                 "Total difere da soma dos títulos", 8, 20, str(resultado["total_centavos"]))

    if info["codigo"] == "756" and info["operacao"] == "Retorno":
        quantidade = conferir_campo(resultado, trailer, numero, "quantidade_detalhes", 164, 171, "numero")

        if resultado["total_completo"] and validar_numerico(quantidade) and int(quantidade) != resultado["detalhes"]:
            adicionar_ocorrencia(resultado, numero, "quantidade_detalhes", quantidade,
                                 "Quantidade difere dos detalhes", 164, 171, str(resultado["detalhes"]))
