# Identifica o layout quando todas as linhas têm um dos tamanhos reconhecidos.
def detectar_layout(linhas):

    if not linhas:
        return "Arquivo vazio"

    # Cria um conjunto com os tamanhos encontrados, eliminando tamanhos repetidos.
    tamanhos = {
        len(linha) 
        for linha in linhas
    }

    layouts = {
        240: "CNAB 240",
        400: "CNAB 400",
        440: "Layout 440",
        500: "Layout 500"
    }

    if len(tamanhos) != 1:
        return "Tamanhos inconsistentes"

    tamanho = tamanhos.pop()

    return layouts.get(
        tamanho,
        "Layout desconhecido"
    )
