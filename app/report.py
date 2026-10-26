import csv
from datetime import datetime
from io import StringIO
from pathlib import Path


# Define as colunas compartilhadas pelo relatório da interface e pelo terminal.
COLUNAS = [
    "linha", "campo", "valor", "classificacao", "motivo",
    "inicio", "fim", "esperado", "referencia",
]


# Evita que textos do arquivo sejam interpretados como fórmulas ao abrir o CSV.
def proteger_celula(valor):

    if isinstance(valor, str) and valor.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + valor

    return valor


# Gera o CSV em memória, com BOM para preservar os acentos em planilhas.
def gerar_csv(ocorrencias):

    saida = StringIO(newline="")
    escritor = csv.DictWriter(saida, fieldnames=COLUNAS, delimiter=";")
    escritor.writeheader()

    for ocorrencia in ocorrencias:
        registro = {}

        for coluna in COLUNAS:
            registro[coluna] = proteger_celula(ocorrencia.get(coluna, ""))

        if not str(registro["valor"]).strip():
            registro["valor"] = "(vazio)"

        escritor.writerow(registro)

    return saida.getvalue().encode("utf-8-sig")


# Salva o relatório sem substituir arquivos já existentes na pasta de saída.
def gerar_relatorio(ocorrencias):

    pasta = Path("relatorios")
    pasta.mkdir(parents=True, exist_ok=True)
    identificador = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    sufixo = 1

    while True:
        caminho = pasta / f"ocorrencias_cnab_{identificador}_{sufixo}.csv"

        try:
            with caminho.open("xb") as arquivo:
                arquivo.write(gerar_csv(ocorrencias))
            return caminho
        except FileExistsError:
            sufixo += 1
