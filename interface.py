# Inicia a versão desktop. A interface Streamlit anterior está em interface_web.py.
from app.desktop import criar_aplicacao


# Mantém o ponto de entrada simples para abrir com Python ou pelo iniciador Windows.
def main():

    janela, estado = criar_aplicacao()
    janela.mainloop()


if __name__ == "__main__":
    main()
