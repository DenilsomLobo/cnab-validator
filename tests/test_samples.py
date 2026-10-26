import json
from pathlib import Path

import pytest

from app.bancos import analisar_bancario
from app.reader import ler_arquivo
from samples.gerar_cnab_bancos import criar_casos, salvar_casos


# Confere as expectativas de cada cenário com o mesmo motor usado pela interface.
@pytest.mark.parametrize("caso", criar_casos(), ids=lambda caso: caso["arquivo"])
def test_casos_cnab(caso):

    resultado = analisar_bancario(caso["linhas"])
    campos = {item["campo"] for item in resultado["erros"]}

    assert resultado["situacao"] == caso["situacao"]
    assert set(caso["campos_erros"]).issubset(campos)

    if not caso["campos_erros"]:
        assert not resultado["erros"]
        assert resultado["total_centavos"] == 46250
        assert resultado["detalhes"] == 3


# Confere os arquivos gravados, incluindo CRLF, quantidade de bytes e manifesto.
def test_arquivos_salvos(tmp_path):

    manifesto = salvar_casos(tmp_path)
    assert len(manifesto) == 39

    for item in manifesto:
        conteudo = (tmp_path / item["arquivo"]).read_bytes()
        linhas, encoding, avisos = ler_arquivo(conteudo)

        if item["arquivo"].endswith("_base.rem") or item["arquivo"].endswith("_base.ret"):
            assert len(linhas) == 5
            assert len(conteudo) == 5 * 402
            assert all(len(linha) == 400 for linha in linhas)
            assert conteudo.count(b"\r\n") == 5

    gravado = json.loads((tmp_path / "resultados_esperados.json").read_text(encoding="utf-8"))
    assert gravado == manifesto


# Garante que os exemplos distribuídos correspondam ao gerador versionado.
def test_exemplos_distribuidos(tmp_path):

    manifesto = salvar_casos(tmp_path)
    pasta = Path(__file__).resolve().parents[1] / "samples" / "bancos"

    for item in manifesto:
        assert (pasta / item["arquivo"]).read_bytes() == (tmp_path / item["arquivo"]).read_bytes()
