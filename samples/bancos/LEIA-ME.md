# Arquivos CNAB 400 para teste local

Estes arquivos são **sintéticos**, com empresas, pagadores, contas e inscrições
inventados. Servem para exercitar o validador deste projeto; não são arquivos
emitidos, homologados ou aprovados pelos bancos e não devem ser enviados a eles.
Campos ainda não verificados pelo programa podem estar incompletos ou fictícios.

## Como testar

1. Abra a interface do projeto e mantenha o banco em identificação automática.
2. Deixe o perfil didático desmarcado.
3. Envie um arquivo desta pasta.
4. Confira as ocorrências e compare com `resultados_esperados.json`.

| Nome do arquivo | Resultado esperado |
| --- | --- |
| `*_remessa_base.rem` | Sem erros nas regras atuais; validação incompleta |
| `*_retorno_base.ret` | Sem erros nas regras atuais; validação incompleta |
| `*_erro_data.rem` | Vencimento impossível na linha 2 |
| `*_erro_sequencia.rem` | Sequência 000099 na linha 2 |
| `*_erro_truncado.rem` | Linha 2 com apenas 120 posições |
| `*_sem_trailer.rem` | Falta o registro final do arquivo |
| `santander_erro_total.rem` | Valor total do trailer divergente |
| `itau_erro_total.ret` | Valor total do trailer divergente |
| `sicoob_erro_quantidade.ret` | Quantidade de detalhes divergente |
| `arquivo_vazio.txt` | Arquivo vazio |

Os arquivos base têm cinco linhas: cabeçalho, três detalhes e trailer.
Os valores nominais são R$ 125,00, R$ 250,00 e R$ 87,50, totalizando R$ 462,50.
Cada registro base possui 400 bytes, com espaços preservados, codificação ASCII
e quebras de linha Windows (CRLF).

Há remessas para Itaú, Bradesco, Santander, Banco do Brasil, Sicoob e Caixa.
Há retornos para todos esses bancos exceto Banco do Brasil: o perfil CBR643
ainda não está implementado e não foi simulado como um retorno oficial.

## Gerar novamente

Na raiz do projeto:

```powershell
.venv\Scripts\python.exe samples\gerar_cnab_bancos.py
```

O comando regrava os exemplos gerados e o pacote `samples/cnab_testes.zip`.
Para alterar um exemplo manualmente, copie-o para outra pasta primeiro.
