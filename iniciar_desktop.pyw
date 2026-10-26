from pathlib import Path
from tkinter import Tk, messagebox


# Inicia sem console e mostra uma mensagem se faltarem dependências ou ocorrer uma falha.
def main():

    try:
        from interface import main as iniciar
        iniciar()
    except Exception as erro:
        import traceback

        caminho = Path(__file__).resolve().parent / "erro_desktop.log"

        try:
            caminho.write_text(traceback.format_exc(), encoding="utf-8")
        except OSError:
            pass

        janela = Tk()
        janela.withdraw()
        messagebox.showerror(
            "CNAB Validator",
            f"Não foi possível abrir o aplicativo.\n\n{erro}\n\n"
            "Instale as dependências com:\n"
            ".venv\\Scripts\\python.exe -m pip install -r requirements.txt\n\n"
            f"Detalhes: {caminho}",
            parent=janela,
        )
        janela.destroy()


if __name__ == "__main__":
    main()
