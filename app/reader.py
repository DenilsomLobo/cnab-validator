"""Leitura sem alterar espaços nem descartar registros vazios internos."""
import codecs


# Converte os bytes em texto sem apagar os espaços usados nas posições dos campos.
def ler_arquivo(conteudo, codificacao="Automática"):
    avisos = []
    if codificacao == "Automática":
        if conteudo.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE,
                                codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
            raise ValueError("UTF-16/UTF-32 não são aceitos. Exporte o arquivo em ASCII ou Windows-1252.")
        try:
            texto = conteudo.decode("utf-8-sig")
            encoding = "UTF-8" if any(b > 127 for b in conteudo) else "ASCII"
        except UnicodeDecodeError:
            encoding = "cp1252"
            try:
                texto = conteudo.decode(encoding)
            except UnicodeDecodeError as exc:
                raise ValueError("Codificação não reconhecida. Escolha a codificação de origem.") from exc
            avisos.append("Windows-1252 presumido; confirme a codificação de origem.")
    else:
        encoding = codificacao
        try:
            texto = conteudo.decode(encoding)
        except (UnicodeDecodeError, LookupError) as exc:
            raise ValueError("O arquivo não pode ser lido com a codificação selecionada.") from exc
    if texto.startswith("\ufeff"):
        texto = texto[1:]
    if conteudo.startswith(codecs.BOM_UTF8):
        avisos.append("BOM UTF-8 removido antes da análise.")
    if any(ord(c) < 32 and c not in "\r\n" for c in texto):
        raise ValueError("O arquivo contém caracteres de controle ou conteúdo binário.")
    # Apenas CR e LF são delimitadores; splitlines também dividiria o byte 0x85.
    linhas = texto.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if linhas and linhas[-1] == "":
        linhas.pop()
    return linhas, encoding, avisos
