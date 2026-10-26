from pathlib import Path

from app.bancos import analisar_bancario
from app.reader import ler_arquivo
from app.report import gerar_relatorio


# Usa o mesmo motor da interface para que o resultado não dependa da forma de execução.
def main():

    print("CNAB Validator — Cobrança CNAB 400")
    caminho = input("Informe o caminho do arquivo CNAB: ").strip().strip('"')

    try:
        linhas, encoding, avisos = ler_arquivo(Path(caminho).read_bytes())
    except (OSError, ValueError) as erro:
        print(f"Não foi possível ler o arquivo: {erro}")
        return

    resultado = analisar_bancario(linhas)
    info = resultado["identificacao"]
    print(f"Banco: {info['banco']} | Movimento: {info['operacao']}")
    print(f"Codificação: {encoding} | Situação: {resultado['situacao']}")

    for aviso in avisos:
        print(f"ALERTA: {aviso}")

    print(f"Válidos nas regras: {resultado['validos']}")
    print(f"Inválidos: {resultado['invalidos']}")
    print(f"Validação incompleta: {resultado['incompletos']}")
    print(f"Erros: {len(resultado['erros'])} | Alertas: {len(resultado['alertas'])}")
    ocorrencias = resultado["erros"] + resultado["alertas"]

    # Mostra as mensagens e grava todas as ocorrências em um único relatório.
    for item in ocorrencias:
        print(f"{item['classificacao']} — linha {item['linha']} — {item['campo']}: {item['motivo']}")

    if ocorrencias:
        print(f"Relatório: {gerar_relatorio(ocorrencias)}")


# Permite importar o módulo em testes sem solicitar entrada no terminal.
if __name__ == "__main__":
    main()
