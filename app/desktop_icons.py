import customtkinter as ctk
from PIL import Image, ImageDraw


# Desenha ícones de linha no próprio aplicativo, sem depender de fontes ou downloads.
# A imagem maior mantém os traços nítidos em telas com escala de exibição elevada.
def criar_icones_menu():

    icones = {}

    for nome in ["Nova análise", "Ocorrências", "Registros", "Bancos e manuais", "Arquivos de teste"]:
        imagem = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
        desenho = ImageDraw.Draw(imagem)
        cor = "white"

        if nome == "Nova análise":
            desenho.line([(10, 41), (10, 7), (29, 7), (38, 16), (38, 41), (10, 41)], fill=cor, width=3)
            desenho.line([(29, 7), (29, 16), (38, 16)], fill=cor, width=3)
            desenho.line([(17, 28), (22, 33), (32, 23)], fill=cor, width=3)

        elif nome == "Ocorrências":
            desenho.line([(24, 7), (43, 40), (5, 40), (24, 7)], fill=cor, width=3)
            desenho.line([(24, 19), (24, 29)], fill=cor, width=3)
            desenho.ellipse((22, 33, 26, 37), fill=cor)

        elif nome == "Registros":
            desenho.rounded_rectangle((7, 8, 41, 40), radius=3, outline=cor, width=3)
            desenho.line([(17, 8), (17, 40)], fill=cor, width=3)

            for altura in (18, 29):
                desenho.line([(7, altura), (41, altura)], fill=cor, width=3)

        elif nome == "Bancos e manuais":
            desenho.line([(5, 17), (24, 6), (43, 17), (5, 17)], fill=cor, width=3)

            for coluna in (12, 24, 36):
                desenho.line([(coluna, 21), (coluna, 35)], fill=cor, width=3)

            desenho.line([(7, 39), (41, 39)], fill=cor, width=3)

        else:
            desenho.line([(6, 39), (6, 11), (21, 11), (26, 17), (42, 17), (42, 39), (6, 39)], fill=cor, width=3)
            desenho.line([(7, 23), (41, 23)], fill=cor, width=3)

        icones[nome] = ctk.CTkImage(light_image=imagem, dark_image=imagem, size=(22, 22))

    return icones
