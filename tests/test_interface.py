from io import BytesIO
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from test_bancos import montar_arquivo
from test_itau import arquivo as arquivo_itau


# Substitui somente o upload para testar a tela real sem usar arquivos bancários pessoais.
def abrir_interface(monkeypatch, linhas):

    arquivo = BytesIO("\n".join(linhas).encode("ascii"))
    arquivo.name = "teste.rem"
    arquivo.size = len(arquivo.getvalue())
    monkeypatch.setattr("streamlit.file_uploader", lambda *args, **kwargs: arquivo)
    caminho = Path(__file__).resolve().parents[1] / "interface_web.py"
    tela = AppTest.from_file(caminho, default_timeout=20).run()
    assert not tela.exception
    return tela


# Garante que os seis bancos podem chegar ao resultado sem erro de execução na interface.
@pytest.mark.parametrize("codigo", ["341", "237", "033", "001", "756", "104"])
def test_resultado_dos_bancos(monkeypatch, codigo):

    linhas = arquivo_itau() if codigo == "341" else montar_arquivo(codigo)
    tela = abrir_interface(monkeypatch, linhas)
    assert len(tela.metric) == 6
    assert tela.metric[2].value == "1"
    assert any("incompleta" in item.value for item in tela.warning)

    # Mostra e oculta a prévia, verificando que o conteúdo preserva seus espaços.
    tela.checkbox[1].check().run()
    assert not tela.exception
    assert tela.code[0].value == "\n".join(linhas[:5])
    tela.checkbox[1].uncheck().run()
    assert not tela.code


# Confirma os estados de arquivo vazio, banco divergente e perfil do exercício original.
def test_vazio_divergencia_e_didatico(monkeypatch):

    tela = abrir_interface(monkeypatch, [])
    assert any("vazio" in item.value for item in tela.error)

    tela = abrir_interface(monkeypatch, montar_arquivo("237"))
    tela.selectbox[0].select("Santander").run()
    assert not tela.exception
    assert tela.metric[1].value == "0"

    from pathlib import Path
    linhas = Path("samples/exemplo.rem").read_text(encoding="latin-1").splitlines()
    tela = abrir_interface(monkeypatch, linhas)
    tela.checkbox[0].check().run()
    assert not tela.exception
    assert tela.metric[3].value == "2"
