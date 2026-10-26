from app.validator import validar_obrigatorio

from app.validator import validar_numerico

def test_campo_preenchido():

    resultado = validar_obrigatorio("123456")
    assert resultado is True

def test_campo_vazio():
    resultado = validar_obrigatorio("    ")

    assert resultado is False  

