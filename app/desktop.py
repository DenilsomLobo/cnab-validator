import os
import queue
import threading
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from app.desktop_service import analisar_caminho, filtrar_ocorrencias
from app.desktop_theme import CORES, configurar_tema
from app.desktop_icons import criar_icones_menu
from app.layouts import BANCOS
from app.report import gerar_csv


# Localiza os exemplos e os documentos usando a pasta do projeto, não a pasta do terminal.
PASTA_PROJETO = Path(__file__).resolve().parents[1]
COLUNAS = ["linha", "classificacao", "campo", "valor", "motivo", "inicio", "fim", "esperado"]


# Cria um botão com o padrão visual do aplicativo e mantém o comando separado da aparência.
def criar_botao(pai, texto, comando, principal=False, **opcoes):

    return ctk.CTkButton(
        pai, text=texto, command=comando, height=38, corner_radius=10,
        font=("Segoe UI", 13),
        fg_color=CORES["azul"] if principal else "#EAF0F8",
        hover_color=CORES["azul_hover"] if principal else "#DCE7F4",
        text_color="white" if principal else CORES["texto"], **opcoes,
    )


# Monta uma tabela com rolagem vertical e horizontal para campos de largura fixa.
def criar_tabela(pai, colunas, titulos, larguras):

    moldura = ctk.CTkFrame(pai, fg_color="white", corner_radius=10)
    moldura.pack(fill="both", expand=True, pady=10)
    moldura.grid_columnconfigure(0, weight=1)
    moldura.grid_rowconfigure(0, weight=1)
    tabela = ttk.Treeview(moldura, columns=colunas, show="headings", style="CNAB.Treeview")

    for coluna, titulo, largura in zip(colunas, titulos, larguras):
        tabela.heading(coluna, text=titulo)
        tabela.column(coluna, width=largura, minwidth=60, stretch=False)

    vertical = ttk.Scrollbar(moldura, orient="vertical", command=tabela.yview)
    horizontal = ttk.Scrollbar(moldura, orient="horizontal", command=tabela.xview)
    tabela.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    tabela.grid(row=0, column=0, sticky="nsew")
    vertical.grid(row=0, column=1, sticky="ns")
    horizontal.grid(row=1, column=0, sticky="ew")
    return tabela


# Troca somente a página visível, preservando os resultados e os controles de navegação.
def abrir_pagina(estado, nome):

    estado["pagina"] = nome

    for pagina, painel in estado["paginas"].items():
        if pagina == nome:
            painel.grid()
        else:
            painel.grid_remove()

    for pagina, botao in estado["botoes_menu"].items():
        botao.configure(fg_color=CORES["azul"] if pagina == nome else "transparent")

    estado["titulo"].configure(text=nome)


# Recolhe o menu sem destruir páginas, como a navegação do TI-Help.
def alternar_menu(estado):

    estado["menu_aberto"] = not estado["menu_aberto"]
    aberto = estado["menu_aberto"]
    estado["menu"].configure(width=238 if aberto else 76)
    estado["marca"].configure(text="CNAB\nVALIDATOR" if aberto else "CN")
    estado["toggle"].configure(text="‹ Recolher menu" if aberto else "›")

    for nome, botao in estado["botoes_menu"].items():
        botao.configure(text=f"  {nome}" if aberto else "",
                        anchor="w" if aberto else "center")


# Seleciona o arquivo com uma janela nativa; cancelar não modifica a análise atual.
def selecionar_arquivo(estado):

    caminho = filedialog.askopenfilename(
        parent=estado["janela"], title="Selecionar arquivo CNAB",
        filetypes=[("Arquivos CNAB", "*.rem *.ret *.txt *.tst *.rst"), ("Todos os arquivos", "*.*")],
    )

    if caminho:
        estado["caminho"].set(caminho)
        limpar_resultado(estado)


# Remove dados antigos quando o arquivo ou as opções mudam, evitando exportar uma análise anterior.
def limpar_resultado(estado):

    estado["analise"] = None
    estado["exportar"].configure(state="disabled")
    estado["resumo"].configure(text="Selecione as opções e clique em Analisar arquivo.")
    estado["status"].set("Pronto para uma nova análise")

    for valor in estado["indicadores"].values():
        valor.configure(text="—")

    for chave in ("tabela_ocorrencias", "tabela_registros"):
        tabela = estado[chave]
        tabela.delete(*tabela.get_children())

    estado["contagem"].configure(text="Nenhuma análise carregada")
    estado["contagem_registros"].configure(text="Nenhuma análise carregada")
    mostrar_previa(estado)


# Executa leitura e validação em segundo plano para manter a janela responsiva.
def iniciar_analise(estado):

    if estado["ocupado"]:
        return

    caminho = estado["caminho"].get().strip()

    if not caminho:
        messagebox.showinfo("Arquivo necessário", "Selecione um arquivo CNAB para analisar.", parent=estado["janela"])
        return

    codigo = None

    for numero, banco in BANCOS.items():
        if banco["nome"] == estado["banco"].get():
            codigo = numero

    codificacao = estado["codificacao"].get()
    limpar_resultado(estado)
    estado["ocupado"] = True
    estado["analisar"].configure(state="disabled")
    estado["selecionar"].configure(state="disabled")
    estado["opcao_banco"].configure(state="disabled")
    estado["opcao_codificacao"].configure(state="disabled")
    estado["status"].set("Analisando arquivo…")
    estado["progresso"].configure(mode="indeterminate")
    estado["progresso"].start()

    # A thread não acessa widgets: entrega o resultado pela fila para a janela principal.
    def executar():
        try:
            analise = analisar_caminho(caminho, codificacao, codigo)
            estado["fila"].put(("resultado", analise))
        except Exception as erro:
            estado["fila"].put(("erro", str(erro)))

    threading.Thread(target=executar, daemon=True).start()


# Consulta a fila no evento da janela; toda atualização visual ocorre na thread principal.
def receber_resultados(estado):

    if estado["fechado"]:
        return

    try:
        tipo, conteudo = estado["fila"].get_nowait()
    except queue.Empty:
        estado["janela"].after(100, lambda: receber_resultados(estado))
        return

    estado["ocupado"] = False
    estado["progresso"].stop()
    estado["progresso"].configure(mode="determinate")
    estado["progresso"].set(0)

    for chave in ("analisar", "selecionar"):
        estado[chave].configure(state="normal")

    for chave in ("opcao_banco", "opcao_codificacao"):
        estado[chave].configure(state="readonly")

    if tipo == "erro":
        estado["status"].set("Não foi possível analisar o arquivo")
        messagebox.showerror("Falha na leitura", conteudo, parent=estado["janela"])
    else:
        apresentar_resultado(estado, conteudo)

    estado["janela"].after(100, lambda: receber_resultados(estado))


# Atualiza os indicadores e os filtros usando o resultado do motor bancário existente.
def apresentar_resultado(estado, analise):

    estado["analise"] = analise
    resultado = analise["resultado"]
    info = resultado["identificacao"]
    valores = {
        "Registros": len(analise["linhas"]), "Válidos nas regras": resultado["validos"],
        "Incompletos": resultado["incompletos"], "Inválidos": resultado["invalidos"],
        "Erros": len(resultado["erros"]), "Alertas": len(resultado["alertas"]),
    }

    for nome, valor in valores.items():
        estado["indicadores"][nome].configure(text=str(valor))

    resumo = (
        f"{analise['nome']}  •  {analise['tamanho_kb']:.2f} KB  •  {analise['codificacao']}\n"
        f"{info['banco']}  •  {info['servico']}  •  {info['operacao']}\n"
        f"Situação: {resultado['situacao']}\nReferência: {info['versao']}"
    )

    if analise["avisos"]:
        resumo += "\n" + "\n".join(analise["avisos"])

    estado["resumo"].configure(text=resumo)
    estado["status"].set(resultado["situacao"])
    estado["exportar"].configure(state="normal")
    ocorrencias = resultado["erros"] + resultado["alertas"]
    estado["filtro_campo"].configure(values=["Todos"] + sorted({item["campo"] for item in ocorrencias}))
    estado["campo"].set("Todos")
    estado["classificacao"].set("Todas")
    estado["busca"].set("")
    atualizar_ocorrencias(estado)
    atualizar_registros(estado, 0)
    mostrar_previa(estado)
    abrir_pagina(estado, "Nova análise")


# Mostra no máximo 200 ocorrências por página sem limitar o relatório exportado.
def atualizar_ocorrencias(estado, pagina=0):

    tabela = estado["tabela_ocorrencias"]
    tabela.delete(*tabela.get_children())

    if not estado["analise"]:
        return

    resultado = estado["analise"]["resultado"]
    ocorrencias = resultado["erros"] + resultado["alertas"]
    filtradas = filtrar_ocorrencias(ocorrencias, estado["classificacao"].get(),
                                   estado["campo"].get(), estado["busca"].get())
    pagina = max(0, min(pagina, max(0, (len(filtradas) - 1) // 200)))
    estado["pagina_ocorrencias"] = pagina

    for item in filtradas[pagina * 200:(pagina + 1) * 200]:
        tabela.insert("", "end", values=[item.get(chave, "") for chave in COLUNAS])

    estado["contagem"].configure(
        text=f"{len(filtradas)} ocorrências filtradas • Página {pagina + 1} de {max(1, (len(filtradas) + 199) // 200)}"
    )


# Exibe registros paginados e mantém uma coluna para os 400 caracteres originais.
def atualizar_registros(estado, pagina=0):

    tabela = estado["tabela_registros"]
    tabela.delete(*tabela.get_children())

    if not estado["analise"]:
        return

    linhas = estado["analise"]["linhas"]
    registros = {item["Linha"]: item for item in estado["analise"]["resultado"]["registros"]}
    pagina = max(0, min(pagina, max(0, (len(linhas) - 1) // 200)))
    estado["pagina_registros"] = pagina

    for numero in range(pagina * 200, min((pagina + 1) * 200, len(linhas))):
        registro = registros.get(numero + 1, {})
        tabela.insert("", "end", values=(numero + 1, registro.get("Tipo", "Não verificado"),
                      registro.get("Situação", "Não verificado"), len(linhas[numero]), linhas[numero]))

    estado["contagem_registros"].configure(
        text=f"{len(linhas)} registros • Página {pagina + 1} de {max(1, (len(linhas) + 199) // 200)}"
    )


# Mostra ou esconde as cinco primeiras linhas em fonte monoespaçada, preservando espaços.
def mostrar_previa(estado):

    texto = estado["previa"]
    texto.configure(state="normal")
    texto.delete("1.0", "end")

    if estado["analise"] and estado["ver_previa"].get():
        texto.insert("1.0", "\n".join(estado["analise"]["linhas"][:5]))
        texto.pack(fill="x", padx=20, pady=(0, 15))
    else:
        texto.pack_forget()

    texto.configure(state="disabled")


# Salva todas as ocorrências com o mesmo CSV da versão anterior, sem aplicar os filtros da tela.
def exportar_relatorio(estado):

    if not estado["analise"]:
        return

    caminho = filedialog.asksaveasfilename(
        parent=estado["janela"], title="Salvar relatório completo", defaultextension=".csv",
        initialfile="ocorrencias_cnab.csv", filetypes=[("Relatório CSV", "*.csv")],
    )

    if not caminho:
        return

    resultado = estado["analise"]["resultado"]

    try:
        Path(caminho).write_bytes(gerar_csv(resultado["erros"] + resultado["alertas"]))
        estado["status"].set(f"Relatório salvo: {caminho}")
    except OSError as erro:
        messagebox.showerror("Falha ao salvar", str(erro), parent=estado["janela"])


# Abre pastas locais pelo gerenciador de arquivos do sistema.
def abrir_pasta(estado, pasta):

    try:
        os.startfile(str(pasta))
    except OSError as erro:
        messagebox.showerror("Não foi possível abrir", str(erro), parent=estado["janela"])


# Encerra o ciclo de consulta da fila antes de destruir a janela.
def fechar_aplicacao(estado):

    estado["fechado"] = True
    estado["janela"].destroy()


# Prepara menu, páginas e estado em dicionários, mantendo o estilo procedural do projeto.
def criar_aplicacao():

    janela = ctk.CTk()
    configurar_tema(janela)
    janela.title("CNAB Validator • Desktop")
    janela.geometry("1240x820")
    janela.minsize(980, 700)
    janela.grid_columnconfigure(1, weight=1)
    janela.grid_rowconfigure(0, weight=1)
    estado = {
        "janela": janela, "analise": None, "ocupado": False, "fechado": False,
        "fila": queue.Queue(), "paginas": {}, "botoes_menu": {}, "menu_aberto": True,
        "caminho": ctk.StringVar(), "banco": ctk.StringVar(value="Identificar automaticamente"),
        "codificacao": ctk.StringVar(value="Automática"), "status": ctk.StringVar(value="Pronto para analisar"),
        "classificacao": ctk.StringVar(value="Todas"), "campo": ctk.StringVar(value="Todos"),
        "busca": ctk.StringVar(), "ver_previa": ctk.BooleanVar(value=False),
        "indicadores": {}, "pagina_ocorrencias": 0, "pagina_registros": 0,
    }

    # A navegação lateral usa a organização do TI-Help com a identidade azul do validador.
    menu = ctk.CTkFrame(janela, width=238, fg_color=CORES["menu"], corner_radius=0)
    menu.grid(row=0, column=0, sticky="ns")
    menu.pack_propagate(False)
    estado["menu"] = menu
    estado["marca"] = ctk.CTkLabel(menu, text="CNAB\nVALIDATOR", text_color="white",
                                   font=("Segoe UI", 23, "bold"), anchor="w")
    estado["marca"].pack(fill="x", padx=20, pady=(30, 24))

    # Mantém as imagens no estado para reutilizá-las com o menu aberto ou recolhido.
    estado["icones_menu"] = criar_icones_menu()

    for nome, icone in estado["icones_menu"].items():
        botao = ctk.CTkButton(menu, text=f"  {nome}", image=icone, compound="left", anchor="w", height=44,
                            fg_color="transparent", hover_color=CORES["menu_hover"],
                            text_color="white", font=("Segoe UI", 13), corner_radius=10,
                            command=lambda pagina=nome: abrir_pagina(estado, pagina))
        botao.pack(fill="x", padx=10, pady=4)
        estado["botoes_menu"][nome] = botao

    estado["toggle"] = ctk.CTkButton(menu, text="‹ Recolher menu", height=36, fg_color="transparent",
                                     hover_color=CORES["menu_hover"], command=lambda: alternar_menu(estado))
    estado["toggle"].pack(side="bottom", fill="x", padx=10, pady=15)
    criar_botao(menu, "Sair", lambda: fechar_aplicacao(estado)).pack(side="bottom", fill="x", padx=10)

    conteudo = ctk.CTkFrame(janela, fg_color=CORES["fundo"], corner_radius=0)
    conteudo.grid(row=0, column=1, sticky="nsew", padx=26, pady=20)
    conteudo.grid_columnconfigure(0, weight=1)
    conteudo.grid_rowconfigure(1, weight=1)
    estado["titulo"] = ctk.CTkLabel(conteudo, text="Nova análise", font=("Segoe UI", 26, "bold"),
                                    text_color=CORES["texto"], anchor="w")
    estado["titulo"].grid(row=0, column=0, sticky="ew", pady=(0, 14))

    for nome in estado["botoes_menu"]:
        painel = ctk.CTkFrame(conteudo, fg_color="transparent")
        painel.grid(row=1, column=0, sticky="nsew")
        estado["paginas"][nome] = painel

    montar_analise(estado)
    montar_ocorrencias(estado)
    montar_registros(estado)
    montar_referencias(estado)
    montar_exemplos(estado)
    ctk.CTkLabel(conteudo, textvariable=estado["status"], anchor="w", text_color=CORES["secundario"],
                 font=("Segoe UI", 12), wraplength=900).grid(row=2, column=0, sticky="ew", pady=(10, 0))
    janela.protocol("WM_DELETE_WINDOW", lambda: fechar_aplicacao(estado))
    janela.bind("<Control-o>", lambda evento: selecionar_arquivo(estado) if not estado["ocupado"] else None)
    janela.bind("<Control-s>", lambda evento: exportar_relatorio(estado))
    abrir_pagina(estado, "Nova análise")
    janela.after(100, lambda: receber_resultados(estado))
    return janela, estado


# Monta o formulário e os cartões de resultado em uma página com rolagem.
def montar_analise(estado):

    painel = ctk.CTkScrollableFrame(estado["paginas"]["Nova análise"], fg_color="transparent")
    painel.pack(fill="both", expand=True)
    card = ctk.CTkFrame(painel, fg_color="white", corner_radius=14, border_width=1, border_color=CORES["borda"])
    card.pack(fill="x", pady=(0, 15))
    ctk.CTkLabel(card, text="Selecione um arquivo para validar", font=("Segoe UI", 18, "bold"),
                 text_color=CORES["texto"]).pack(anchor="w", padx=20, pady=(18, 10))
    linha = ctk.CTkFrame(card, fg_color="transparent")
    linha.pack(fill="x", padx=20, pady=5)
    # O caminho é somente leitura; a seleção sempre passa pela janela de arquivos.
    ctk.CTkEntry(linha, textvariable=estado["caminho"], height=38, state="readonly").pack(side="left", fill="x", expand=True, padx=(0, 10))
    estado["selecionar"] = criar_botao(linha, "Selecionar…", lambda: selecionar_arquivo(estado))
    estado["selecionar"].pack(side="right")
    opcoes = ctk.CTkFrame(card, fg_color="transparent")
    opcoes.pack(fill="x", padx=20, pady=12)
    ctk.CTkLabel(opcoes, text="Banco", text_color=CORES["secundario"]).pack(side="left", padx=(0, 8))
    estado["opcao_banco"] = ctk.CTkComboBox(opcoes, variable=estado["banco"], width=230, state="readonly",
        values=["Identificar automaticamente"] + [b["nome"] for b in BANCOS.values()], command=lambda valor: limpar_resultado(estado))
    estado["opcao_banco"].pack(side="left", padx=(0, 14))
    estado["opcao_codificacao"] = ctk.CTkComboBox(opcoes, variable=estado["codificacao"], width=145, state="readonly",
        values=["Automática", "ascii", "utf-8-sig", "cp1252", "latin-1"], command=lambda valor: limpar_resultado(estado))
    estado["opcao_codificacao"].pack(side="left")
    estado["analisar"] = criar_botao(card, "Analisar arquivo", lambda: iniciar_analise(estado), True)
    estado["analisar"].pack(anchor="w", padx=20, pady=(0, 12))
    estado["progresso"] = ctk.CTkProgressBar(card, mode="determinate", height=4)
    estado["progresso"].pack(fill="x", padx=20, pady=(0, 15))
    estado["progresso"].set(0)
    estado["resumo"] = ctk.CTkLabel(painel, text="Selecione as opções e clique em Analisar arquivo.",
        anchor="w", justify="left", wraplength=680, text_color=CORES["texto"], font=("Segoe UI", 13))
    estado["resumo"].pack(fill="x", pady=(0, 15))
    grade = ctk.CTkFrame(painel, fg_color="transparent")
    grade.pack(fill="x")

    for coluna in range(3):
        grade.grid_columnconfigure(coluna, weight=1, uniform="cartoes")

    for indice, nome in enumerate(["Registros", "Válidos nas regras", "Incompletos", "Inválidos", "Erros", "Alertas"]):
        card = ctk.CTkFrame(grade, fg_color="white", corner_radius=12, border_width=1, border_color=CORES["borda"])
        card.grid(row=indice // 3, column=indice % 3, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(card, text=nome, text_color=CORES["secundario"], font=("Segoe UI", 12)).pack(anchor="w", padx=15, pady=(12, 0))
        valor = ctk.CTkLabel(card, text="—", font=("Segoe UI", 27, "bold"), text_color=CORES["texto"])
        valor.pack(anchor="w", padx=15, pady=(0, 12))
        estado["indicadores"][nome] = valor

    ctk.CTkCheckBox(painel, text="Mostrar as primeiras cinco linhas", variable=estado["ver_previa"],
                    command=lambda: mostrar_previa(estado), text_color=CORES["texto"]).pack(anchor="w", pady=15)
    estado["previa"] = ctk.CTkTextbox(painel, height=150, wrap="none", font=("Consolas", 12), state="disabled")
    ctk.CTkLabel(painel, text="Validação incompleta significa que há regras ainda não verificadas. Consulte Ocorrências.",
                 text_color=CORES["secundario"], wraplength=680).pack(anchor="w", pady=10)


# Monta filtros, paginação e exportação para a lista de erros e alertas.
def montar_ocorrencias(estado):

    painel = estado["paginas"]["Ocorrências"]
    filtros = ctk.CTkFrame(painel, fg_color="transparent")
    filtros.pack(fill="x")
    ctk.CTkComboBox(filtros, variable=estado["classificacao"], values=["Todas", "ERRO", "ALERTA"],
        state="readonly", width=120, command=lambda valor: atualizar_ocorrencias(estado)).pack(side="left", padx=(0, 8))
    estado["filtro_campo"] = ctk.CTkComboBox(filtros, variable=estado["campo"], values=["Todos"],
        state="readonly", width=170, command=lambda valor: atualizar_ocorrencias(estado))
    estado["filtro_campo"].pack(side="left", padx=(0, 8))
    busca = ctk.CTkEntry(filtros, textvariable=estado["busca"], placeholder_text="Buscar ocorrências")
    busca.pack(side="left", fill="x", expand=True, padx=(0, 8))
    busca.bind("<Return>", lambda evento: atualizar_ocorrencias(estado))
    criar_botao(filtros, "Filtrar", lambda: atualizar_ocorrencias(estado), width=80).pack(side="left")
    estado["tabela_ocorrencias"] = criar_tabela(painel, COLUNAS,
        ["Linha", "Classificação", "Campo", "Valor", "Motivo", "Início", "Fim", "Esperado"],
        [65, 105, 150, 170, 420, 65, 65, 250])
    rodape = ctk.CTkFrame(painel, fg_color="transparent")
    rodape.pack(fill="x")
    estado["contagem"] = ctk.CTkLabel(rodape, text="Nenhuma análise carregada", text_color=CORES["secundario"])
    estado["contagem"].pack(side="left")
    criar_botao(rodape, "‹", lambda: atualizar_ocorrencias(estado, estado["pagina_ocorrencias"] - 1), width=36).pack(side="left", padx=6)
    criar_botao(rodape, "›", lambda: atualizar_ocorrencias(estado, estado["pagina_ocorrencias"] + 1), width=36).pack(side="left")
    estado["exportar"] = criar_botao(rodape, "Exportar CSV completo", lambda: exportar_relatorio(estado), True)
    estado["exportar"].configure(state="disabled")
    estado["exportar"].pack(side="right")


# Monta a consulta aos registros, incluindo o texto original sem remover espaços.
def montar_registros(estado):

    painel = estado["paginas"]["Registros"]
    ctk.CTkLabel(painel, text="Use a rolagem horizontal para consultar o registro completo.",
                 text_color=CORES["secundario"]).pack(anchor="w")
    estado["tabela_registros"] = criar_tabela(painel,
        ["linha", "tipo", "situacao", "tamanho", "conteudo"],
        ["Linha", "Tipo", "Situação", "Caracteres", "Conteúdo original"], [65, 130, 225, 95, 3000])
    linha = ctk.CTkFrame(painel, fg_color="transparent")
    linha.pack(fill="x")
    estado["contagem_registros"] = ctk.CTkLabel(linha, text="Nenhuma análise carregada", text_color=CORES["secundario"])
    estado["contagem_registros"].pack(side="left")
    criar_botao(linha, "Anterior", lambda: atualizar_registros(estado, estado["pagina_registros"] - 1), width=90).pack(side="right", padx=5)
    criar_botao(linha, "Próxima", lambda: atualizar_registros(estado, estado["pagina_registros"] + 1), width=90).pack(side="right")


# Apresenta a versão e o link dos manuais com a cobertura já documentada pelo projeto.
def montar_referencias(estado):

    painel = ctk.CTkScrollableFrame(estado["paginas"]["Bancos e manuais"], fg_color="transparent")
    painel.pack(fill="both", expand=True)

    for codigo, banco in BANCOS.items():
        card = ctk.CTkFrame(painel, fg_color="white", corner_radius=12)
        card.pack(fill="x", pady=6)
        ctk.CTkLabel(card, text=f"{codigo} • {banco['nome']}", font=("Segoe UI", 17, "bold"),
                     text_color=CORES["texto"]).pack(anchor="w", padx=18, pady=(15, 0))
        ctk.CTkLabel(card, text=banco["versao"], wraplength=640, justify="left",
                     text_color=CORES["secundario"]).pack(anchor="w", padx=18, pady=6)
        criar_botao(card, "Abrir manual oficial", lambda url=banco["manual"]: webbrowser.open(url)).pack(anchor="w", padx=18, pady=(0, 15))

    ctk.CTkLabel(painel, text="Cobertura parcial de cobrança CNAB 400. Retorno CBR643 do BB e CNAB 240 ainda não cobertos.",
                 text_color=CORES["secundario"], wraplength=680).pack(anchor="w", pady=15)


# Dá acesso aos exemplos existentes sem depender de download ou conexão com a internet.
def montar_exemplos(estado):

    painel = estado["paginas"]["Arquivos de teste"]
    ctk.CTkLabel(painel, text="39 cenários para testar a validação", font=("Segoe UI", 20, "bold"),
                 text_color=CORES["texto"]).pack(anchor="w", pady=(10, 15))
    ctk.CTkLabel(painel, text="Dados fictícios para uso local. Os arquivos base não são homologados pelos bancos.\n"
                 "Selecione um arquivo *_remessa_base.rem para começar; os arquivos com erro exercitam as falhas.",
                 justify="left", wraplength=680, text_color=CORES["secundario"]).pack(anchor="w", pady=10)
    criar_botao(painel, "Abrir pasta dos arquivos", lambda: abrir_pasta(estado, PASTA_PROJETO / "samples" / "bancos"), True).pack(anchor="w", pady=10)
    criar_botao(painel, "Abrir guia dos testes", lambda: abrir_pasta(estado, PASTA_PROJETO / "samples" / "bancos" / "LEIA-ME.md")).pack(anchor="w", pady=5)
