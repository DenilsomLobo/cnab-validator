# Classifica cada registro sem misturar erros com verificações ainda incompletas.
# Um alerta não invalida a linha, mas impede que ela seja apresentada como totalmente verificada.
def classificar_resultado(resultado, linhas):

    linhas_invalidas = set()
    linhas_incompletas = set()

    for erro in resultado["erros"]:
        if erro["linha"] > 0:
            linhas_invalidas.add(erro["linha"])

    for alerta in resultado["alertas"]:
        if alerta["linha"] == 0:
            linhas_incompletas.update(range(1, len(linhas) + 1))
        else:
            linhas_incompletas.add(alerta["linha"])

    if not resultado["identificacao"]["suportado"]:
        linhas_incompletas.update(range(1, len(linhas) + 1))

    # Dá prioridade ao erro quando a mesma linha também possui um alerta.
    linhas_incompletas.difference_update(linhas_invalidas)

    resultado["invalidos"] = len(linhas_invalidas)
    resultado["incompletos"] = len(linhas_incompletas)
    resultado["validos"] = len(linhas) - resultado["invalidos"] - resultado["incompletos"]

    # Guarda o estado de cada linha para a tabela de registros da interface.
    for registro in resultado["registros"]:
        numero = registro["Linha"]

        if numero in linhas_invalidas:
            registro["Situação"] = "Inválido"
        elif numero in linhas_incompletas:
            registro["Situação"] = "Validação incompleta"
        else:
            registro["Situação"] = "Válido nas regras executadas"

    # Erros do arquivo, como arquivo vazio, também afetam a situação geral.
    if resultado["erros"]:
        resultado["situacao"] = "Inválido"
    elif resultado["incompletos"] or resultado["alertas"]:
        resultado["situacao"] = "Validação incompleta"
    else:
        resultado["situacao"] = "Válido nas regras executadas"

    return resultado
