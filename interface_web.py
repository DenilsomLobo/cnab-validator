from pathlib import Path

import streamlit as st

from app.bancos import analisar_bancario
from app.detector import detectar_layout
from app.layouts import BANCOS
from app.parser import interpretar_registro
from app.reader import ler_arquivo
from app.report import gerar_csv
from app.validator import validar_registro


# Mantém o exercício original disponível sem aplicar suas posições aos layouts bancários.
def analisar_arquivo(linhas):

    erros = []
    alertas = []
    validos = 0

    for numero, linha in enumerate(linhas, start=1):

        if len(linha) != 400:
            erros.append({
                "linha": numero,
                "campo": "registro",
                "valor": str(len(linha)),
                "classificacao": "ERRO",
                "motivo": "Tamanho diferente de 400",
            })
            continue

        ocorrencias = validar_registro(interpretar_registro(linha), numero)
        erros_registro = []

        # Somente a classificação ERRO torna um registro inválido.
        for ocorrencia in ocorrencias:
            if ocorrencia["classificacao"] == "ERRO":
                erros_registro.append(ocorrencia)
            else:
                alertas.append(ocorrencia)

        erros.extend(erros_registro)

        if not erros_registro:
            validos += 1

    return {
        "validos": validos,
        "invalidos": len(linhas) - validos,
        "incompletos": 0,
        "erros": erros,
        "alertas": alertas,
    }


# Aplica a paleta azul-marinho, azul e branco sem esconder os controles do Streamlit.
def aplicar_estilo():

    st.markdown("""
    <style>
        .stApp {background: #f5f8fc; color: #102b4e;}
        .stMainBlockContainer {max-width: 1180px; padding-top: 2.4rem;}
        h1, h2, h3 {color: #102b4e; letter-spacing: -0.025em;}
        h1 {font-size: 2.7rem;}
        [data-testid="stMetric"] {
            background: white; border: 1px solid #dce7f3;
            border-top: 3px solid #2374d8; border-radius: 12px; padding: 18px;
        }
        [data-testid="stMetricLabel"] {color: #506580;}
        [data-testid="stMetricValue"] {color: #102b4e;}
        [data-testid="stVerticalBlockBorderWrapper"] {border-radius: 12px;}
        [data-testid="stFileUploaderDropzone"] {background: white; border: 1px dashed #8fb4df;}
        .identidade {font-size: .75rem; font-weight: 700; color: #2374d8;
                     letter-spacing: .16em; margin-bottom: .4rem;}
        @media (max-width: 640px) {
            .stMainBlockContainer {padding-top: 1rem;}
            h1 {font-size: 2rem;}
        }
    </style>
    """, unsafe_allow_html=True)


# Exibe as ocorrências com filtros sem alterar os dados do relatório completo.
def mostrar_ocorrencias(resultado):

    ocorrencias = resultado["erros"] + resultado["alertas"]

    if not ocorrencias:
        st.success("Nenhuma ocorrência encontrada nas regras executadas.")
        return

    st.subheader("Ocorrências")
    col1, col2 = st.columns(2)

    with col1:
        classificacao = st.selectbox("Classificação", ["Todas", "ERRO", "ALERTA"])

    with col2:
        campos = sorted({item["campo"] for item in ocorrencias})
        campo = st.selectbox("Campo", ["Todos"] + campos)

    filtradas = []

    for item in ocorrencias:
        mesma_classificacao = classificacao == "Todas" or item["classificacao"] == classificacao
        mesmo_campo = campo == "Todos" or item["campo"] == campo

        if mesma_classificacao and mesmo_campo:
            filtradas.append(item)

    st.caption(f"Exibindo {len(filtradas)} de {len(ocorrencias)} ocorrências.")
    st.dataframe(filtradas, hide_index=True, width="stretch", column_config={
        "linha": "Linha", "campo": "Campo", "valor": "Valor encontrado",
        "classificacao": "Classificação", "motivo": "Motivo",
        "inicio": "Posição inicial", "fim": "Posição final",
        "esperado": "Formato esperado", "referencia": "Manual",
    })
    st.download_button(
        "Baixar relatório completo", gerar_csv(ocorrencias),
        file_name="ocorrencias_cnab.csv", mime="text/csv", type="primary",
    )
    st.caption("O relatório inclui erros e alertas, independentemente dos filtros.")


# Monta a tela de envio, executa a análise e apresenta o resultado ao usuário.
def main():

    st.set_page_config(page_title="CNAB Validator", page_icon="📄", layout="wide")
    aplicar_estilo()

    st.markdown('<div class="identidade">ARQUIVOS BANCÁRIOS</div>', unsafe_allow_html=True)
    st.title("CNAB Validator")
    st.write("Valide a estrutura do arquivo e encontre os campos que precisam de atenção.")
    st.caption("Itaú · Bradesco · Santander · Banco do Brasil · Sicoob · Caixa")
    st.divider()

    envio, ajuda = st.columns([2, 1], gap="large")

    with envio:
        st.subheader("Envie seu arquivo")
        opcoes = ["Identificar automaticamente"]
        opcoes.extend(banco["nome"] for banco in BANCOS.values())
        selecionado = st.selectbox("Banco", opcoes)
        arquivo = st.file_uploader("Arquivo CNAB", type=["rem", "ret", "txt", "tst", "rst"])

        # Mantém opções menos usadas recolhidas para simplificar a tela principal.
        with st.expander("Opções de leitura"):
            codificacao = st.selectbox("Codificação", ["Automática", "ascii", "utf-8-sig", "cp1252", "latin-1"])
            didatico = st.checkbox("Usar o perfil do exemplo didático")

    with ajuda:
        with st.container(border=True):
            st.markdown("**Como interpretar o resultado**")
            st.write("**Inválido:** foram encontrados erros.")
            st.write("**Validação incompleta:** existem regras ainda não verificadas.")
            st.write("**Válido nas regras executadas:** as verificações aplicadas passaram.")
            st.caption("Cobrança CNAB 400. A versão do manual e a cobertura aparecem na análise.")

            # Disponibiliza os cenários sintéticos dos bancos para testar o upload.
            pacote_testes = Path(__file__).parent / "samples" / "cnab_testes.zip"

            if pacote_testes.exists():
                st.download_button(
                    "Baixar CNABs para teste", pacote_testes.read_bytes(),
                    file_name="cnab_testes.zip", mime="application/zip",
                )
                st.caption("Dados fictícios para teste local. Extraia o ZIP e envie um arquivo base ou com erro.")

            exemplo = Path(__file__).parent / "samples" / "exemplo.rem"

            if exemplo.exists():
                st.download_button("Baixar exemplo didático", exemplo.read_bytes(), file_name="exemplo.rem")
                st.caption("Para esse arquivo, ative o perfil didático nas opções de leitura.")

    if arquivo is None:
        st.info("Selecione um arquivo para começar a análise.")
        return

    # Exibe o tamanho em KB e preserva o nome recebido pelo componente de upload.
    st.text(f"{arquivo.name} • {arquivo.size / 1024:.2f} KB")

    try:
        linhas, encoding, avisos = ler_arquivo(arquivo.getvalue(), codificacao)
    except ValueError as erro:
        st.error(str(erro))
        return

    st.caption(f"Formato: {detectar_layout(linhas)} • Codificação: {encoding}")

    for aviso in avisos:
        st.info(aviso)

    # A visualização é opcional e não remove os espaços das primeiras cinco linhas.
    if st.checkbox("Mostrar as primeiras cinco linhas do arquivo"):
        st.code("\n".join(linhas[:5]), language="text")

    banco_esperado = None

    for codigo, banco in BANCOS.items():
        if banco["nome"] == selecionado:
            banco_esperado = codigo

    with st.spinner("Analisando registros…"):
        if didatico:
            resultado = analisar_arquivo(linhas)
            st.warning("Perfil didático: as posições deste exercício não representam um layout bancário oficial.")
        else:
            resultado = analisar_bancario(linhas, banco_esperado)

    st.divider()
    st.subheader("Resultado da análise")

    if not linhas:
        st.error("O arquivo está vazio.")
        return

    # Apresenta a identificação e as limitações do perfil antes dos indicadores.
    if not didatico:
        info = resultado["identificacao"]
        st.text(f"{info['banco']} • {info['servico']} • {info['operacao']}")
        st.caption(f"Referência: {info['versao']}")

        if info["manual"]:
            st.markdown(f"[Consultar manual de referência]({info['manual']})")

        if resultado["situacao"] == "Inválido":
            st.error("Arquivo com erros. Consulte as ocorrências abaixo.")
        elif resultado["situacao"] == "Validação incompleta":
            st.warning("Validação incompleta. Confira as regras pendentes nas ocorrências.")
        else:
            st.success("As regras executadas passaram.")

    # Separa os três estados para que alertas não sejam contados como erros ou aprovação.
    indicadores = [
        ("Registros", len(linhas)),
        ("Válidos nas regras", resultado["validos"]),
        ("Validação incompleta", resultado["incompletos"]),
        ("Inválidos", resultado["invalidos"]),
        ("Erros", len(resultado["erros"])),
        ("Alertas", len(resultado["alertas"])),
    ]

    for inicio in (0, 3):
        colunas = st.columns(3)

        for coluna, (titulo, valor) in zip(colunas, indicadores[inicio:inicio + 3]):
            coluna.metric(titulo, valor)

    if not didatico and resultado["registros"]:
        with st.expander("Consultar registros identificados"):
            st.dataframe(resultado["registros"], hide_index=True, width="stretch")

        if not resultado["total_completo"]:
            st.caption("A soma dos valores está incompleta por registros ou variantes sem cobertura.")

    mostrar_ocorrencias(resultado)


# Executa a interface somente quando este arquivo é o ponto de entrada.
if __name__ == "__main__":
    main()
