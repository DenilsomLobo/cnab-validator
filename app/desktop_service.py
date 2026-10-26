from pathlib import Path

from app.bancos import analisar_bancario
from app.reader import ler_arquivo


# Lê o arquivo e chama o mesmo validador utilizado pelo terminal e pela versão web.
# Esta função não cria widgets, permitindo executá-la fora da thread da janela.
def analisar_caminho(caminho, codificacao="Automática", banco_esperado=None):

    caminho = Path(caminho)
    conteudo = caminho.read_bytes()
    linhas, encoding, avisos = ler_arquivo(conteudo, codificacao)
    resultado = analisar_bancario(linhas, banco_esperado)

    return {
        "nome": caminho.name,
        "caminho": str(caminho.resolve()),
        "tamanho_kb": len(conteudo) / 1024,
        "linhas": linhas,
        "codificacao": encoding,
        "avisos": avisos,
        "resultado": resultado,
    }


# Filtra ocorrências sem alterar a lista original que será exportada no relatório.
def filtrar_ocorrencias(ocorrencias, classificacao="Todas", campo="Todos", busca=""):

    filtradas = []
    busca = busca.strip().casefold()

    for item in ocorrencias:
        mesma_classificacao = classificacao == "Todas" or item["classificacao"] == classificacao
        mesmo_campo = campo == "Todos" or item["campo"] == campo
        texto = " ".join(str(valor) for valor in item.values()).casefold()

        if mesma_classificacao and mesmo_campo and (not busca or busca in texto):
            filtradas.append(item)

    return filtradas
