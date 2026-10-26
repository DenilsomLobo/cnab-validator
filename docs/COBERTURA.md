# Cobertura da validação

O projeto implementa verificações locais de estrutura e campos principais de
cobrança CNAB 400. Cada perfil possui seu próprio mapa de posições, movimento e
referência de manual em [`app/layouts.py`](../app/layouts.py).

## Referências

| Banco | Edição consultada | Fonte |
| --- | --- | --- |
| Itaú | Janeiro/2017 | [Manual CNAB 400](https://download.itau.com.br/bankline/layout_cobranca_400bytes_cnab_itau.pdf) |
| Bradesco | 4008.524.0121 v17, 28/09/2020 | [Manual de cobrança](https://banco.bradesco/assets/pessoajuridica/pdf/4008-524-0121-layout-cobranca-versao-portugues.pdf) |
| Santander | H7800 v2.37, fevereiro/2026 | [Layouts oficiais](https://www.santander.com.br/layout-de-arquivos) |
| Banco do Brasil | CBR641, junho/2024 | [Manual de remessa](https://www.bb.com.br/docs/pub/emp/empl/dwn/Doc2627CBR641Pos7.pdf) |
| Sicoob | Abas CNAB400 da planilha publicada em 19/05/2025 | [Planilha oficial](https://www.sicoob.com.br/documents/20128/263767178/Layout_Cobranca_CNAB240.xls/d3b63439-cf63-67bc-8282-e89abda79eb0?download=true) |
| Caixa | SIGCB 67.126 v029 | [Manual CNAB 400](https://www.caixa.gov.br/Downloads/cobranca-caixa/Manual_de_Leiaute_de_Arquivo_Eletronico_CNAB_400.pdf) |

As cópias locais dos manuais não são distribuídas neste repositório. A edição
adotada pela conta deve ser confirmada junto ao banco.

## Verificações

- Banco, serviço e movimento identificados pelo conteúdo do cabeçalho.
- Cabeçalho único no início e trailer único no final.
- Tipos de registro, comprimento e sequência conforme o perfil.
- Formato de campos numéricos, datas e conteúdos fixos previstos no código.
- Totais Itaú no retorno, Santander na remessa e quantidade Sicoob no retorno.
- Separação entre registros inválidos, incompletos e válidos nas regras executadas.

## Limitações

Não estão completamente cobertos: dígitos verificadores, condições de carteira,
convênio e contratação, comandos específicos, tabelas de rejeição, rateio,
mensagens, Pix e outros complementos. O retorno CBR643 do Banco do Brasil e a
validação bancária de CNAB 240 não estão implementados.

Um alerta de cobertura não invalida a linha, mas impede classificá-la como
completamente verificada. A aprovação nas regras executadas não substitui a
homologação do banco. Os testes do repositório usam arquivos sintéticos.
