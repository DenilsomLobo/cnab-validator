# Guarda o nome, a versão e o manual de cada banco separado das regras de validação.
# As posições abaixo começam em 1 e incluem a posição final, como nos manuais.
BANCOS = {
    "341": {
        "nome": "Itaú", "versao": "Janeiro/2017",
        "manual": "https://download.itau.com.br/bankline/layout_cobranca_400bytes_cnab_itau.pdf",
        "detalhe_remessa": "1", "detalhe_retorno": "1",
        "tipos_remessa": "012459", "tipos_retorno": "0149",
    },
    "237": {
        "nome": "Bradesco", "versao": "4008.524.0121 v17 — 28/09/2020",
        "manual": "https://banco.bradesco/assets/pessoajuridica/pdf/4008-524-0121-layout-cobranca-versao-portugues.pdf",
        "detalhe_remessa": "1", "detalhe_retorno": "1",
        "tipos_remessa": "0123679", "tipos_retorno": "0139",
    },
    "033": {
        "nome": "Santander", "versao": "H7800 v2.37 — Fevereiro/2026",
        "manual": "https://www.santander.com.br/layout-de-arquivos",
        "detalhe_remessa": "1", "detalhe_retorno": "1",
        "tipos_remessa": "012456789", "tipos_retorno": "0129",
    },
    "001": {
        "nome": "Banco do Brasil", "versao": "CBR641 — Junho/2024 — convênio acima de 1.000.000",
        "manual": "https://www.bb.com.br/docs/pub/emp/empl/dwn/Doc2627CBR641Pos7.pdf",
        "detalhe_remessa": "7", "detalhe_retorno": None,
        "tipos_remessa": "0759", "tipos_retorno": "",
    },
    "756": {
        "nome": "Sicoob", "versao": "Planilha oficial publicada em 19/05/2025 — abas CNAB400",
        "manual": "https://www.sicoob.com.br/documents/20128/263767178/Layout_Cobranca_CNAB240.xls/d3b63439-cf63-67bc-8282-e89abda79eb0?download=true",
        "detalhe_remessa": "1", "detalhe_retorno": "1",
        "tipos_remessa": "019", "tipos_retorno": "019",
    },
    "104": {
        "nome": "Caixa Econômica Federal", "versao": "SIGCB 67.126 v029",
        "manual": "https://www.caixa.gov.br/Downloads/cobranca-caixa/Manual_de_Leiaute_de_Arquivo_Eletronico_CNAB_400.pdf",
        "detalhe_remessa": "1", "detalhe_retorno": "1",
        "tipos_remessa": "012459", "tipos_retorno": "019",
    },
}


# Cada campo informa: nome, início, fim e regra usada pelo motor de validação.
# Datas e valores só são exigidos na entrada de títulos, pois comandos têm outras condições.
CAMPOS_REMESSA = {
    "237": [
        ("empresa", 21, 37, "numero"),
        ("nosso_numero", 71, 81, "numero"),
        ("ocorrencia", 109, 110, "numero"),
    ],
    "033": [
        ("agencia", 18, 21, "numero"),
        ("conta_movimento", 22, 29, "numero"),
        ("conta_cobranca", 30, 37, "numero"),
        ("nosso_numero", 63, 70, "numero"),
        ("ocorrencia", 109, 110, "numero"),
    ],
    "001": [
        ("inscricao", 4, 17, "numero"),
        ("agencia", 18, 21, "numero"),
        ("conta", 23, 30, "numero"),
        ("convenio", 32, 38, "numero"),
        ("nosso_numero", 64, 80, "numero"),
        ("carteira", 107, 108, "numero"),
        ("ocorrencia", 109, 110, "numero"),
    ],
    "756": [
        ("inscricao", 4, 17, "numero"),
        ("cooperativa", 18, 21, "numero"),
        ("conta", 23, 30, "numero"),
        ("nosso_numero", 63, 74, "numero"),
        ("carteira", 107, 108, "numero"),
        ("ocorrencia", 109, 110, "numero"),
    ],
    "104": [
        ("inscricao", 4, 17, "numero"),
        ("beneficiario", 21, 27, "numero"),
        ("nosso_numero", 57, 73, "numero"),
        ("carteira", 107, 108, "numero"),
        ("ocorrencia", 109, 110, "numero"),
    ],
}


# Define os campos de retorno separadamente para não reutilizar posições da remessa.
CAMPOS_RETORNO = {
    "237": [("empresa", 21, 37, "numero"), ("nosso_numero", 71, 81, "numero")],
    "033": [("agencia", 18, 21, "numero"), ("conta_movimento", 22, 29, "numero"),
            ("conta_cobranca", 30, 37, "numero"), ("nosso_numero", 63, 70, "numero")],
    "756": [("cooperativa", 18, 21, "numero"), ("conta", 23, 30, "numero"),
            ("nosso_numero", 63, 73, "numero")],
    "104": [("beneficiario", 21, 27, "numero"), ("nosso_numero", 57, 73, "numero")],
}
