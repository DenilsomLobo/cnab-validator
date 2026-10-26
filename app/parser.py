# Extrai um campo usando posições inclusivas contadas a partir de 1.
def extrair_campo(linha,inicio,fim):
    return linha[inicio -1:fim]

# Separa os campos de uma linha conforme as posições definidas.
def interpretar_registro(linha):

    tipo = extrair_campo(linha, 1, 1)
    agencia = extrair_campo(linha, 2, 5)
    conta = extrair_campo(linha, 6, 13)
    nosso_numero = extrair_campo(linha, 14, 24)
    vencimento = extrair_campo(linha, 25, 30)
    valor = extrair_campo(linha, 31, 41)
    return{
        "tipo": tipo,
        "agencia": agencia,
        "conta": conta,
        "nosso_numero": nosso_numero,
        "vencimento": vencimento,
        "valor": valor
    }

# Converte um valor em centavos escrito como texto para uma apresentação em reais.
def formatar_valor(valor):

    numero = int(valor) / 100
    formatado = f"{numero:,.2f}"
    formatado = formatado.replace(",", "X")
    formatado = formatado.replace(".", ",")
    formatado = formatado.replace("X", ".")
    return f"R$ {formatado}"
