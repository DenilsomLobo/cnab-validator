import time
from pathlib import Path

import pytest

from app.desktop_service import analisar_caminho, filtrar_ocorrencias


PASTA = Path(__file__).resolve().parents[1]


# Verifica a leitura dos mesmos exemplos na camada independente da interface desktop.
@pytest.mark.parametrize("banco", ["itau", "bradesco", "santander", "banco_do_brasil", "sicoob", "caixa"])
def test_servico_desktop(banco):

    caminho = PASTA / "samples" / "bancos" / f"{banco}_remessa_base.rem"
    analise = analisar_caminho(caminho)
    assert analise["resultado"]["situacao"] == "Validação incompleta"
    assert analise["resultado"]["erros"] == []
    assert len(analise["linhas"]) == 5
    assert analise["tamanho_kb"] == caminho.stat().st_size / 1024


# Confirma que filtrar na tela não remove ocorrências do relatório completo.
def test_filtros_desktop():

    analise = analisar_caminho(PASTA / "samples" / "bancos" / "itau_erro_data.rem")
    resultado = analise["resultado"]
    ocorrencias = resultado["erros"] + resultado["alertas"]
    filtradas = filtrar_ocorrencias(ocorrencias, "ERRO", "vencimento", "INVÁLID")
    assert len(filtradas) == 1
    assert len(ocorrencias) > len(filtradas)


# Exercita widgets reais, processamento assíncrono, navegação, paginação e exportação.
def test_janela_desktop(monkeypatch, tmp_path):

    from app.desktop import (
        criar_aplicacao, iniciar_analise, abrir_pagina, alternar_menu,
        atualizar_ocorrencias, exportar_relatorio, limpar_resultado, fechar_aplicacao,
    )

    janela, estado = criar_aplicacao()
    janela.withdraw()

    try:
        estado["caminho"].set(str(PASTA / "samples" / "bancos" / "santander_erro_total.rem"))
        iniciar_analise(estado)
        limite = time.monotonic() + 10

        # Processa o loop real do Tk até que a thread entregue a análise.
        while estado["ocupado"] and time.monotonic() < limite:
            janela.update()
            time.sleep(0.01)

        assert not estado["ocupado"]
        assert estado["analise"]["resultado"]["situacao"] == "Inválido"
        assert estado["indicadores"]["Registros"].cget("text") == "5"
        abrir_pagina(estado, "Ocorrências")
        estado["classificacao"].set("ERRO")
        atualizar_ocorrencias(estado)
        assert len(estado["tabela_ocorrencias"].get_children()) == 1
        alternar_menu(estado)
        assert not estado["menu_aberto"]
        alternar_menu(estado)
        assert estado["menu_aberto"]
        estado["ver_previa"].set(True)
        from app.desktop import mostrar_previa
        mostrar_previa(estado)
        assert estado["previa"].get("1.0", "end-1c") == "\n".join(estado["analise"]["linhas"][:5])

        destino = tmp_path / "relatorio.csv"
        monkeypatch.setattr("app.desktop.filedialog.asksaveasfilename", lambda **opcoes: str(destino))
        exportar_relatorio(estado)
        assert "valor_total" in destino.read_text(encoding="utf-8-sig")
        assert "cobertura" in destino.read_text(encoding="utf-8-sig")
        limpar_resultado(estado)
        assert estado["analise"] is None
        assert not estado["tabela_ocorrencias"].get_children()
        assert estado["exportar"].cget("state") == "disabled"

        # Uma leitura que falha não pode deixar resultados antigos disponíveis para exportação.
        mensagens = []
        monkeypatch.setattr("app.desktop.messagebox.showerror", lambda *args, **opcoes: mensagens.append(args))
        estado["caminho"].set(str(tmp_path / "inexistente.rem"))
        iniciar_analise(estado)
        limite = time.monotonic() + 10

        while estado["ocupado"] and time.monotonic() < limite:
            janela.update()
            time.sleep(0.01)

        assert mensagens
        assert estado["analise"] is None
        assert estado["exportar"].cget("state") == "disabled"
    finally:
        fechar_aplicacao(estado)
        # Libera variáveis Tk na thread principal antes dos testes web usarem outras threads.
        import gc
        estado.clear()
        del janela
        gc.collect()
