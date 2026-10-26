from datetime import datetime

# Verifica se um campo está vazio
def validar_obrigatorio(valor):

    if valor.strip() == "":
        return False

    return True

# Verifica os campos numéricos
def validar_numerico(valor):

    if not valor.isascii():
        return False

    return valor.isdigit()

#Validar data
def validar_data(valor):

    if len(valor) != 6:
        return False

    if not validar_numerico(valor):
        return False

    try:
        datetime.strptime(valor, "%d%m%y")
        return True

    except ValueError:
        return False

# Validar conta
def validar_conta(valor):

    if len(valor) != 8:
        return False

    return validar_numerico(valor)

#Validar registro
def validar_tipo_registro(valor):
    return valor == "1"

# Validar valores monetários
def validar_valor(valor):

    if len(valor) != 11:
        return False

    if not validar_numerico(valor):
        return False

    if int(valor) <= 0:
        return False

    return True


# ----------------------------------------------  Motor de validação ------------------------------------------ #
def validar_registro(dados, numero_linha):

    erros = []

    def adicionar_erro(campo, motivo):

        erros.append({
            "linha": numero_linha,
            "campo": campo,
            "valor": dados[campo],
            "classificacao": "ERRO",
            "motivo": motivo
        })

    if not validar_tipo_registro(dados["tipo"]):
        adicionar_erro(
            "tipo",
            "Tipo de registro inválido"
        )

    if not validar_conta(dados["conta"]):
        adicionar_erro(
            "conta",
            "Conta inválida"
        )

    if not validar_obrigatorio(dados["nosso_numero"]):
        adicionar_erro(
            "nosso_numero",
            "Campo obrigatório vazio"
        )

    elif not validar_numerico(dados["nosso_numero"]):

        adicionar_erro(
            "nosso_numero",
            "Campo deve conter apenas números"
        )

    if not validar_numerico(dados["agencia"]):
        adicionar_erro(
            "agencia",
            "Agência inválida"
        )

    if not validar_data(dados["vencimento"]):
        adicionar_erro(
            "vencimento",
            "Data de vencimento inválida"
        )

    if not validar_valor(dados["valor"]):

        adicionar_erro("valor", "Valor inválido")

    return erros
