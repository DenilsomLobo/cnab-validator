import customtkinter as ctk
from tkinter import ttk


# Centraliza as cores para que menus, botões e tabelas mantenham o mesmo padrão.
CORES = {
    "fundo": "#F3F6FB",
    "menu": "#102B4E",
    "menu_hover": "#1B416E",
    "azul": "#2374D8",
    "azul_hover": "#1759AB",
    "superficie": "#FFFFFF",
    "borda": "#DCE5F0",
    "texto": "#102B4E",
    "secundario": "#586E88",
}


# Configura o CustomTkinter e a tabela nativa antes de montar as páginas.
def configurar_tema(janela):

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    janela.configure(fg_color=CORES["fundo"])
    estilo = ttk.Style(janela)
    estilo.theme_use("clam")
    estilo.configure("CNAB.Treeview", background="white", foreground=CORES["texto"],
                     fieldbackground="white", rowheight=32, font=("Segoe UI", 10),
                     borderwidth=0)
    estilo.configure("CNAB.Treeview.Heading", background="#EAF0F8", foreground=CORES["texto"],
                     font=("Segoe UI", 10, "bold"), padding=9)
    estilo.map("CNAB.Treeview", background=[("selected", "#D8E9FF")],
               foreground=[("selected", CORES["texto"])])
