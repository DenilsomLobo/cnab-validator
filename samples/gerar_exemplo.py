from pathlib import Path


def criar_registro(
    nosso_numero,
    vencimento,
    valor
):

    tipo = "1"
    agencia = "1234"
    conta = "12345678"

    registro = (
        tipo
        + agencia
        + conta
        + nosso_numero
        + vencimento
        + valor
    )

    return registro.ljust(400)


registro1 = criar_registro(
    "00000123456",
    "151126",
    "00000125000"
)

registro2 = criar_registro(
    "00000123457",
    "321326",
    "00000125000"
)

registro3 = criar_registro(
    "           ",
    "201126",
    "00000085000"
)

pasta = Path("samples")
pasta.mkdir(exist_ok=True)

arquivo = pasta / "exemplo.rem"

with open(arquivo, "w", encoding="ascii") as f:
    f.write(registro1 + "\n")
    f.write(registro2 + "\n")
    f.write(registro3 + "\n")

print("Arquivo de teste criado!")