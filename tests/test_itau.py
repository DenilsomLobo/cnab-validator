import codecs
import unittest

from app.itau import analisar_itau
from app.reader import ler_arquivo


def registro(campos, sequencia):
    linha = list(" " * 400)
    for inicio, valor in campos.items():
        linha[inicio - 1:inicio - 1 + len(valor)] = valor
    linha[394:400] = f"{sequencia:06d}"
    return "".join(linha)


def arquivo(retorno=False):
    header = registro({1:"02RETORNO" if retorno else "01REMESSA",10:"01",12:"COBRANCA".ljust(15),
        27:"1234",31:"00",33:"12345",38:"6",77:"341",95:"261026",
        **({109:"00001",114:"261026"} if retorno else {})},1)
    campos = {1:"1",2:"02",4:"12345678000190",18:"1234",22:"00",24:"12345",29:"6",63:"12345678"}
    if retorno:
        campos.update({83:"109",109:"06",111:"261026",147:"271026",153:"0000000012500",
            176:"0"*13,215:"0"*13,228:"0"*13,241:"0"*13,254:"0000000012500",
            267:"0"*13,280:"0"*13,296:"271026"})
        trailer = registro({1:"9201341",18:"0"*22,58:"0"*22,178:"0"*22,
            208:"00001",213:"00000001",221:"00000000012500"},3)
    else:
        campos.update({71:"0"*13,84:"109",109:"01",121:"271026",127:"0000000012500",
            140:"341",143:"00000",150:"N",151:"261026",161:"0"*13,174:"000000",180:"0"*13,
            193:"0"*13,206:"0"*13,219:"02",221:"12345678000190",235:"PAGADOR",
            275:"RUA EXEMPLO",327:"01001000",335:"SAO PAULO"})
        trailer = registro({1:"9"},3)
    return [header,registro(campos,2),trailer]


class ItauTests(unittest.TestCase):
    def test_remessa_retorno(self):
        for retorno in (False,True):
            with self.subTest(retorno=retorno):
                r = analisar_itau(arquivo(retorno))
                self.assertEqual(r['erros'], [])
                self.assertEqual(r['validos'],3)
                self.assertEqual(r['total_centavos'],12500)

    def test_truncamento_sequencia_e_estrutura(self):
        linhas = arquivo()
        linhas[1] = linhas[1][:120]
        self.assertTrue(any(e['campo']=='registro' for e in analisar_itau(linhas)['erros']))
        linhas = arquivo()
        linhas[1] = linhas[1][:394] + '000009'
        self.assertTrue(any(e['campo']=='sequencia' for e in analisar_itau(linhas)['erros']))
        self.assertTrue(any(e['campo']=='trailer' for e in analisar_itau(arquivo()[:-1])['erros']))

    def test_totais_divergentes(self):
        linhas = arquivo(True)
        linhas[-1] = linhas[-1][:212] + '00000002' + '00000000012501' + linhas[-1][234:]
        campos = {e['campo'] for e in analisar_itau(linhas)['erros']}
        self.assertIn('quantidade_detalhes',campos)
        self.assertIn('valor_total',campos)

    def test_saldos_nao_sao_totais_do_arquivo(self):
        linhas = arquivo(True)
        linhas[-1] = linhas[-1][:17] + '99999999' + '99999999999999' + linhas[-1][39:]
        self.assertEqual(analisar_itau(linhas)['erros'],[])

    def test_perfil_nao_identificado(self):
        self.assertFalse(analisar_itau(['1' * 400])['identificacao']['suportado'])
        self.assertEqual(analisar_itau(['1' * 400])['validos'],0)
        self.assertTrue(analisar_itau([])['erros'])

    def test_alerta_nao_invalida(self):
        linhas = arquivo()
        linhas.insert(2,registro({1:'5'},3))
        linhas[-1] = registro({1:'9'},4)
        r = analisar_itau(linhas)
        self.assertEqual(r['erros'],[])
        self.assertTrue(r['alertas'])
        self.assertEqual(r['validos'],4)

    def test_codificacoes_e_espacos(self):
        for separador in ('\n','\r','\r\n'):
            dados = (separador.join(arquivo()) + separador).encode('ascii')
            self.assertEqual(ler_arquivo(dados)[0],arquivo())
        self.assertEqual(ler_arquivo(b'')[0],[])
        self.assertEqual(ler_arquivo(b'  \n\n')[0],['  ',''])
        self.assertEqual(ler_arquivo(codecs.BOM_UTF8+b'abc')[0],['abc'])
        self.assertEqual(ler_arquivo(b'A\x85B','latin-1')[0],['A\x85B'])
        with self.assertRaises(ValueError):
            ler_arquivo('abc'.encode('utf-16'))
        with self.assertRaises(ValueError):
            ler_arquivo(b'abc\x00')


if __name__ == '__main__':
    unittest.main()
