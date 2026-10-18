# Auditoria independente — V0.2 Data Intelligence Engine

| Item | Valor |
|---|---|
| Escopo | motor V0.2 (`powerbi_autopilot/`), contratos documentados e suíte oficial |
| Commit-base | `c31195d` — branch `qa/v0.2-deepspeek` (worktree limpo no início) |
| Data da auditoria | 2026-10-18 |
| Ambiente | Windows 10/11, CPython, pandas, openpyxl, `unittest`. Sem Power BI Desktop, sem rede, sem bases reais |
| Método | leitura integral do código e dos contratos + sondas adversariais + suíte independente em `tests/qa_external/` |
| Alterações em código de produção | **nenhuma** (auditoria somente leitura) |
| Alterações em testes existentes | **nenhuma** (suíte oficial intocada) |

## Veredito

**Aprovado com restrições — não recomendado para uso em bases reais sem as correções P0.**

O motor é arquiteturalmente sólido no que promete: falha fechado, nunca inventa valor,
mantém fato/inferência/hipótese separados, não vaza células nas saídas, preserva bytes e é
determinístico. Esses pontos foram atacados de propósito e resistiram (seção 5).

O problema está no **vocabulário de reconhecimento**, não na disciplina de evidência. Quatro
defeitos rejeitam ou bloqueiam arquivos comuns e legítimos: uma tabela qualquer que tenha
coluna chamada `Tipo`/`Status` recebe BLOCKER financeiro que não existe (QA-F01), cabeçalhos
corriqueiros como `Valor Total` e `Data de Pagamento` não são mapeados e geram BLOCKER de
pagamento sem data (QA-F03), CSV de uma coluna exportado em pt-BR é recusado como irregular
(QA-F16) e um workbook válido com um gráfico é recusado como "corrompido/protegido" (QA-F05).
Em uso real, o veredito do produto seria "bloqueado" por motivos que não são dos dados.

## 1. Baseline e como reproduzir

```
python -m unittest discover -s tests -v          # suíte oficial: 53 testes, OK, ~2 s, exit 0
python -m unittest discover -s tests/qa_external -v   # suíte desta auditoria: 79 testes
```

`tests/qa_external/` não possui `__init__.py`, portanto **não** é coletado por
`discover -s tests`: o baseline oficial permanece 53 testes e não muda de significado depois
desta auditoria. A suíte independente é executada explicitamente pelo segundo comando.

Resultado desta auditoria (contagens estáveis; o tempo varia com a máquina):

```
Ran 79 tests in 7.772s
OK (expected failures=7)
```

Os 7 `expectedFailure` **são** os defeitos documentados aqui (QA-F01 ×2, QA-F03, QA-F04,
QA-F05, QA-F08b, QA-F09). Eles passam a "unexpected success" no dia em que o defeito for
corrigido — o sinal é intencional: remova o decorador junto com a correção.

## 2. Suíte independente entregue

Todos os dados são sintéticos, criados em diretório temporário; nenhum fixture do repositório
é reutilizado e nenhum módulo de produção é importado de forma que altere estado.

| Arquivo | Testes | Foco |
|---|---:|---|
| `tests/qa_external/test_qa_parsing.py` | 13 | números/datas ambíguos, locale explícito, anotações de moeda, NaN/infinito, separador de milhar |
| `tests/qa_external/test_qa_financial.py` | 13 | esquema completo limpo, moeda/movimento/status, fallback por nome, cabeçalhos reais |
| `tests/qa_external/test_qa_relationships.py` | 8 | cardinalidade, órfãos, nulos, limite de candidatos, pares intra-tabela |
| `tests/qa_external/test_qa_intake.py` | 13 | CSV (BOM, cabeçalho duplicado/vazio, cotação, rodapé, delimitador), XLSX (abas ocultas/vazias, fórmulas, chartsheet, `header_row`) |
| `tests/qa_external/test_qa_engine.py` | 13 | artefatos, determinismo, contrato de ocorrência, duplicatas preservadas, integridade da fonte, CLI (exit 0/1/2, `--overwrite`) |
| `tests/qa_external/test_qa_semantics.py` | 8 | hipóteses sem confirmação, limiar de 80 %, supressão de papel genérico, regra extensível |
| `tests/qa_external/test_qa_validation.py` | 11 | precedência de status, reconciliação por identidade, totais em string decimal, limites de evidência |
| **Total** | **79** | |

Convenções: helper `table()` cria `Table` sintética com `row_numbers` reais; `codes()` extrai
apenas códigos de ocorrência; nenhum teste imprime valor de célula.

## 3. Defeitos e riscos — resumo

Severidade combina probabilidade de ocorrência em arquivo real com dano ao veredito do produto
(bloqueio indevido, perda de mapeamento, número errado silencioso).

| ID | Classificação | Sev. | Sintoma observado | Código | Teste |
|---|---|---|---|---|---|
| QA-F01 | BUG CONFIRMADO | **P0 / ALTA** | tabela não financeira com `Tipo`/`Status` recebe `unknown_movement_type` e `unknown_payment_status` como BLOCKER | `financial.py:32-39` | `test_qa_f01_*` (2, xfail) |
| QA-F03 | BUG CONFIRMADO | **P0 / ALTA** | `Valor Total` e `Data de Pagamento` não são mapeados → BLOCKER `paid_without_payment_date` em arquivo limpo | `semantics.py:59`, `financial.py:39` | `test_qa_f03_*` (xfail) |
| QA-F16 | BUG CONFIRMADO | **P0 / ALTA (pt-BR)** | CSV de uma coluna com vírgula decimal é recusado como "campos incompatíveis" | `intake.py:88` | `test_single_column_csv_with_decimal_comma_is_rejected` |
| QA-F05 | BUG CONFIRMADO | P1 / MÉDIA | workbook válido com 1 chartsheet é recusado como "inválida, protegida ou ilegível" | `intake.py:120-122, 147-148` | `test_qa_f05_*` (xfail) |
| QA-F04 | BUG CONFIRMADO | P1 / MÉDIA | `multiplication_risk` assimétrico por nulos → `join_multiplication_risk` BLOCKER em uma direção só | `relationships.py:40` | `test_qa_f04_*` (xfail) |
| QA-F08b | BUG PROVÁVEL | P1 / MÉDIA | coluna `Status` com `1/0` vira `payment_status` (0,85) → `paid_without_payment_date` para toda linha `1` | `semantics.py:11-12` | `test_qa_f08b_*` (xfail) |
| QA-F09 | BUG PROVÁVEL | P2 / BAIXA-MÉDIA | `0,500` sob `en-US` (e `0.500` sob `pt-BR`) é aceito como 500: magnificação silenciosa de 1000× | `parsing.py:70, 88-91` | `test_qa_f09_*` (xfail) |
| QA-F08 | LACUNA DE VOCABULÁRIO | P2 / MÉDIA | `Em aberto`, `Aguardando`, `Parcial`, `Baixado`… não reconhecidos → BLOCKER por linha | `semantics.py:11-13` | `test_unknown_status_blocks_cash_metrics_with_row_evidence` |
| QA-F14 | RISCO DE DESENHO | P2 / MÉDIA | linha `Total` no fim é ingerida como registro; rodapé irregular recusa o arquivo inteiro | `intake.py:100-110` | `test_footer_total_row_is_ingested_as_a_regular_record` |
| QA-F15 | LIMITAÇÃO ASSUMIDA | P3 / BAIXA | pares de chave na mesma tabela (`Cliente_ID`/`Vendedor_ID`) nunca são candidatos; chaves compostas não existem | `relationships.py:11-19` | `test_intra_table_column_pairs_are_never_candidates` |
| QA-F02 | **CONTROLE (correto)** | — | data mapeada com valor inválido continua bloqueando | `financial.py:56` | `test_qa_f02_*` (ok) |

Identificadores QA-F06, QA-F07 e QA-F10…QA-F13 foram usados na triagem e absorvidos pelos
achados acima (não são defeitos independentes); a numeração dos testes foi mantida estável para
não reescrever os arquivos entregues.

## 4. Fichas

### QA-F01 — fallback por nome reclassifica colunas não financeiras (P0)

**Evidência no código.** `financial.py:32-39` resolve papéis por *nome* quando o mapeamento
semântico não os forneceu:

```python
def named(aliases):
    cols = [c for c in df.columns if normalize(c) in aliases]
    return cols[0] if len(cols) == 1 else None

movement = one('movement_type') or named({'tipo', 'natureza', 'movement_type'})
status   = one('payment_status') or named({'pago', 'status', 'situacao', 'payment_status'})
pay_date = one('payment_date')   or named({'data_pagamento', 'payment_date', 'data_recebimento'})
```

Em seguida `financial.py:44-58` transforma qualquer valor fora de `MOVEMENTS` e
`PAID|PENDING|CANCELLED` em BLOCKER. O fallback ignora a evidência de valores que `map_columns`
**já havia recusado**: em `semantics.py:59-80` uma coluna `Status` com `Concluído`/`Em andamento`
fica `insufficient_evidence` (0 % de tokens plausíveis) e mesmo assim é promovida por nome.

**Sintoma observado.** Tabela `Tarefa | Responsável | Status` (`Concluído`, `Em andamento`):
`unknown_payment_status` BLOCKER, `count=2`, escopo `cash_metrics`, linhas referenciadas.
`Tipo` = `PF`/`PJ` + `Status` = `Ativo`/`Inativo` (cadastro de clientes): `unknown_movement_type`
**e** `unknown_payment_status` como BLOCKER em uma tabela sem fluxo financeiro.

**Impacto.** `engine.py:28,37` soma as ocorrências financeiras de toda tabela à lista global e
`validation.summarize` marca `blocked_scopes` quando existe qualquer BLOCKER. Ou seja: **uma aba
de tarefas, cadastro ou estoque contamina o relatório inteiro** e o produto declara os dados
"bloqueados" sem que exista valor monetário envolvido. O domínio já se declara `hypothesis`
(`financial.py:131`), mas a severidade não acompanha essa incerteza.

**Repro mínimo.**

```python
import pandas as pd
from powerbi_autopilot.contracts import Table
from powerbi_autopilot.profiling import profile_table
from powerbi_autopilot.semantics import map_columns
from powerbi_autopilot import financial

df = pd.DataFrame({'Tarefa': ['A'], 'Status': ['Concluído']})
t = Table('t', df, {'file': 'qa.csv', 'sheet': None, 'sha256': 'x'}, [2])
p = profile_table(t)
print([(i['code'], i['severity']) for i in financial.diagnose(t, p, map_columns(t, p))['issues']])
# [('unknown_payment_status', 'BLOCKER')]
```

**Correção sugerida (não implementada).** Derivar `movement/status/pay_date` **somente** de
`mapping`. Se o fallback por nome for mantido como rede de segurança, exigi-lo condicionado a
evidência financeira observada (`monetary`/papel `amount` presente) e, quando usado, rebaixar a
ocorrência para `INFO`/`WARNING` com `evidence_kind='unknown'`. Alternativa mais alinhada ao
contrato: emitir uma única ocorrência agregada de "status não interpretável" (bloqueando só o
indicador de caixa) em vez de reclassificar a tabela inteira.

### QA-F03 — aliases exigem nome inteiro; cabeçalhos usuais ficam fora (P0)

**Evidência no código.** `semantics.py:59`:

```python
name_match = any(normalized == a or (len(a) >= 4 and normalized.endswith('_' + a)) for a in rule.aliases)
```

A comparação é igualdade (ou sufixo `_alias`). `normalize('Valor Total')` → `valor_total`, que
não é alias de `amount`; `normalize('Data de Pagamento')` → `data_de_pagamento`, que não é alias
de `payment_date`. Não há remoção de conectivos nem contenção por token.

**Sintoma observado.** Planilha limpa com `Valor Total`, `Tipo`, `Moeda`, `Status`,
`Data de Pagamento`: `amount` e `payment_date` não são mapeados. Como `financial.py:39` também
não reconhece o nome, `pay_date` fica `None` e `financial.py:56` marca **toda** linha `Pago`
como `paid_without_payment_date` (BLOCKER). Os indicadores caem para `insufficient_evidence` e
`requirements['amount']` fica falso.

**Impacto.** É o layout mais comum de planilha financeira brasileira. O produto rejeita dados
corretos e a mensagem ("pagamento declarado sem data de pagamento utilizável") aponta um
problema inexistente. Diferente de QA-F01, a perda é dupla: papel não reconhecido **e** BLOCKER
falso.

**Repro mínimo.** Mesma receita da ficha anterior com
`{'Valor Total': ['100,00'], 'Status': ['Pago'], 'Data de Pagamento': ['2026-01-05']}` →
`paid_without_payment_date` BLOCKER, sem `amount`/`payment_date` nos papéis.

**Correção sugerida.** Normalizar conectivos (`de`, `da`, `do`, `das`, `dos`, `e`) antes da
comparação e aceitar contenção por token (`valor_total`, `total_da_nota`, `data_pagamento`,
`data_de_pagamento`, `dt_pagto`). Toda ampliação deve continuar exigindo evidência de valores
(o papel é hipótese) e vir com teste negativo para nomes enganosos (`Total de Itens`,
`Data de Cadastro`).

### QA-F16 — CSV de uma coluna com vírgula decimal é recusado (P0, pt-BR)

**Evidência no código.** `intake.py:84-94` usa `csv.Sniffer().sniff(sample, delimiters=',;\t|')`;
se o sniffer falhar, `sep` cai em `','` (linha 94). Num arquivo de uma coluna cujos valores usam
vírgula decimal (`Valor` / `1.234,56`), a vírgula é o caractere mais frequente e é escolhida como
delimitador — não porque separe campos. O cabeçalho passa a ter 1 campo e as linhas 2, e
`intake.py:107-108` levanta `InputError('Quantidade de campos incompatível na linha 2')`.

**Sintoma observado.** `Valor\n1000,00\n2000,00` → recusa; `Valor;Obs\n1000,00;a\n2000,00;b` →
aceito. O erro aponta a linha 2 de um arquivo íntegro e não menciona delimitador, então o usuário
tende a "corrigir" os dados em vez do diagnóstico. Três sondas desta auditoria tiveram de ganhar
uma segunda coluna artificial só para conseguir chegar ao motor — sinal de que o atrito aparece
antes de qualquer análise.

**Repro mínimo.** `python -m powerbi_autopilot.cli one_column.csv --output out` com o conteúdo
acima → exit 2 e mensagem de campos incompatíveis.

**Correção sugerida.** Exigir que o delimitador candidato apareça no cabeçalho ou validar a
contagem de campos com o delimitador escolhido e, em caso de inconsistência, tentar os demais
candidatos (incluindo "nenhum separador") antes de recusar. Alternativa mínima e segura:
quando todas as linhas menos a primeira tiverem a mesma contagem e o cabeçalho tiver 1 campo,
tratar como arquivo de coluna única e registrar `INFO` (delimitador não aplicável) em vez de erro.

### QA-F05 — chartsheet invalida o workbook inteiro (P1)

**Evidência no código.** `intake.py:120-122` itera `workbook.worksheets` e trata toda planilha
como tabular; `intake.py:147-148` converte **qualquer** exceção em
`InputError('Planilha inválida, protegida ou ilegível')`.

**Sintoma observado.** Workbook com uma aba de dados e um gráfico (chartsheet): nenhuma tabela é
retornada, o arquivo é recusado como corrompido/protegido. O mesmo acontece com qualquer erro
interno inesperado do leitor — a causa real é mascarada.

**Impacto.** Perda total de um arquivo válido por um elemento que o motor nem precisa ler, com
mensagem que induz o usuário a procurar corrupção ou senha. É também um risco de diagnóstico:
bugs internos passam a se apresentar como "arquivo ruim".

**Correção sugerida.** Filtrar por `isinstance(ws, Worksheet)` (ou `hasattr(ws, 'iter_rows')`) e
registrar `INFO` para abas não tabulares; reduzir o `except` a `InvalidFileException`,
`BadZipFile` e `KeyError` de cabeçalho, deixando exceções inesperadas propagarem como erro
interno.

### QA-F04 — `multiplication_risk` assimétrico por nulos (P1)

**Evidência no código.** `relationships.py:33-40` calcula o risco em uma única direção:

```python
left_nulls = len(left.frame)-sum(ls.values())
right_nulls = len(right.frame)-sum(rs.values())
...
'multiplication_risk': join_rows > matched or (left_nulls > 0 and right_nulls > 1),
```

A primeira cláusula é simétrica (só é verdadeira se houver chave repetida de algum lado); a
segunda não. Com `A.Cliente_ID = ['1', None]` e `B.Cliente_ID = ['1', None, None]`, o par `A→B`
recebe `multiplication_risk=True` (`left_nulls=1`, `right_nulls=2`) e `B→A` recebe `False`
(`right_nulls=1` não passa de `> 1`), embora `matched_join_rows == matched == 1` nas duas
direções: **nenhuma multiplicação é observada** em nenhuma delas.

**Sintoma observado.** `multiplication_risk` difere entre `A→B` e `B→A` para os mesmos dados;
`engine.py:41-44` converte o sinal em `join_multiplication_risk` **BLOCKER** com `count=1`,
herdando a assimetria. O usuário vê um BLOCKER de "pode multiplicar registros e valores" em uma
relação que não multiplica nada, e o resultado depende da ordem das tabelas na linha de comando.

**Impacto.** Duas propriedades que o produto promete ficam frágeis: severidade calibrada e
determinismo semântico. Nulos não multiplicam linhas — eles simplesmente não casam, e já são
reportados em `null_source_rows`/`null_target_rows` e em `orphan_rows`.

**Correção sugerida.** Remover a cláusula de nulos de `multiplication_risk` (o risco de nulo já
tem campo próprio) ou separá-la em `null_risk`, simétrica e informativa. Se o comportamento for
mantido, documentar em `docs/DATA_CONTRACTS.md` que o sinal é direcional — hoje o contrato não
menciona a assimetria.

### QA-F08b — bandeira `1/0` aceita como status de pagamento (P1)

**Evidência no código.** `semantics.py:11-12`:

```python
PAID = {'sim', 'true', '1', 'pago', 'paid', 'recebido', 'liquidado', 's', 'yes', '✓'}
PENDING = {'nao', 'false', '0', 'pendente', 'pending', 'aberto', 'n', 'no', 'vencido'}
```

Como `ratio` é tokens reconhecidos / total (linhas 74-76), uma coluna `Status` com `1`/`0` atinge
100 % de cobertura e é sugerida como `payment_status` com confiança **0,70**
(`status='hypothesis'`). `financial.py:37` a adota e `financial.py:53-58` passa a tratá-la como
vocabulário de pagamento.

**Sintoma observado.** `Status` = `1`,`0` em tabela de receita/despesa → `paid_without_payment_date`
BLOCKER (`count=1`), `requirements['payment_status']=True` e `requirements['payment_date']=False`.
Numa coluna de controle (`ativo`, `tem_anexo`, `excluido`), o efeito é o mesmo: `1` vira "pago".

**Impacto.** É a mesma classe de erro de QA-F01, mas por valor em vez de nome, e afeta
`cash_metrics` de uma tabela que **é** financeira — portanto passa despercebido como "só mais um
BLOCKER". Bandeiras booleanas são onipresentes em exports de ERP/CRM.

**Repro.** `test_qa_f08b_numeric_flag_is_not_a_payment_status` (xfail).

**Correção sugerida.** Não tratar `'1'/'0'/'s'/'n'` como vocabulário de status quando a coluna for
integralmente binária; mapear para o tipo `boolean` que o perfil já calcula, ou exigir nome de
bandeira de pagamento (`pago`, `paid`, `quitado`, `liquidado`) para interpretar `1` como pago.
A decisão precisa de contrato explícito: `1` não significa "pago" por si.

### QA-F09 — separador de milhar com zero à esquerda aceito (P2)

**Evidência no código.** `parsing.py:88-91`:

```python
pattern = rf'(?:\d+|\d{{1,3}}(?:{grouping}\d{{3}})+)(?:\{decimal_sep}\d+)?'
```

O primeiro ramo (`\d+`) aceita qualquer sequência e o segundo aceita grupo inicial `0`, então
`0,500` sob `en-US` casa como "0 mil, 500" → `canonical='0500'` → `Decimal('500')`.

**Sintoma observado.**

```
number('0,500', 'en-US')  -> Decimal('500')   # deveria ser inválido
number('0.500', 'pt-BR')  -> Decimal('500')   # espelhado, mesma causa
number('0,500')           -> ambiguous        # sem locale o motor se protege
```

Logo, sem `--locale` não há dano; com locale explícito, um valor escrito na convenção oposta é
convertido com fator 1000 e reportado como `valid` (nenhum aviso). Valores ≥ 1.000 não são
afetados; o dano exige o padrão `0<sep><3 dígitos>`.

**Impacto.** Erro de magnitude silencioso — exatamente o que o contrato de parsing promete
impedir ("não inventar valores"). Só se manifesta com locale declarado (erro de configuração do
usuário), mas o motor tem evidência suficiente para recusar o padrão.

**Correção sugerida.** Rejeitar zero à esquerda em grupo de milhar (`(?:[1-9]\d{0,2})(?:,\d{3})+`),
mantendo `0` isolado e `0,50` inválido sob `en-US`. Testar os dois sentidos (pt-BR e en-US).

### QA-F08 — vocabulário de status incompleto gera BLOCKER por linha (P2)

**Evidência.** `semantics.py:11-13` cobre 12 tokens pt-BR; `financial.py:53-55` transforma
qualquer token fora do conjunto em `unknown_payment_status` **BLOCKER** com as linhas afetadas.

**Sintoma observado.** `Em aberto` → BLOCKER `count=1`, `source_rows=[2]`, escopo `cash_metrics`;
`cash_received` passa a exigir `payment_status`. O mesmo ocorreria com `Aguardando`, `Parcial`,
`Pago parcial`, `Baixado`, `Em análise`, `Pendente de aprovação`, `Em aberto (vencido)` — todos
comuns em exports brasileiros. Note também que `vencido` está em `PENDING`: vencido é atraso, não
pendência genérica, e o motor perde essa distinção (impacto direto no indicador `overdue`).

**Impacto.** O bloqueio é seguro, mas caro: o usuário precisa de um dicionário de sinônimos que o
produto não publica. A mensagem não nomeia o token problemático (política de não expor valores),
então a correção vira tentativa e erro.

**Correção sugerida.** Publicar o vocabulário aceito em `docs/DATA_CONTRACTS.md` e na mensagem;
ampliar o conjunto (`em aberto`, `aguardando`, `parcial`, `pago parcial`, `baixado`, `em análise`,
`em processamento`); separar `overdue` de `pending`, já que `overdue` é indicador próprio. Manter
BLOCKER por linha é aceitável — o defeito é a cobertura estreita, não a severidade.

### QA-F14 — sem detecção de linha de total/rodapé (P2)

**Evidência.** `intake.py:103-110` aceita toda linha com contagem de campos igual à do cabeçalho;
não há heurística de rodapé.

**Sintoma observado.** Arquivo com `Total` na primeira coluna e valor na coluna monetária:

- campos alinhados → a linha entra como **registro** (`row_numbers=[2,3]`), sem ocorrência; o
  perfil passa a incluir um valor que é soma, e qualquer agregação futura conta duas vezes;
- rodapé irregular (`Total;;1.000,00`) → `Quantidade de campos incompatível` e o arquivo inteiro
  é recusado.

**Impacto.** Hoje o V0.2 não soma nada, então o dano é perfil enganoso e risco para V0.3+. A
assimetria (silêncio vs recusa total) é o ponto mais perigoso: o mesmo rodapé produz respostas
opostas dependendo de um `;` a mais.

**Correção sugerida.** Emitir `WARNING`/`INFO` (`footer_row_suspected`) quando a última linha
tiver rótulo em `{total, totais, soma, subtotal, resultado}` e colunas de identidade/data vazias;
nunca remover automaticamente. Para o caso irregular, mensagem específica indicando rodapé
provável em vez de erro genérico de campos.

### QA-F15 — pares intra-tabela e chaves compostas não são considerados (P3)

**Evidência.** `relationships.py:11-14` ignora `left is right`, e `relationships.py:17-20` exige
nome normalizado idêntico e dica de identificador em ambos os lados.

**Sintoma observado.** `Cliente_ID`/`Vendedor_ID` na mesma tabela → `candidates=[]`,
`examined_pairs=0`. Chaves compostas (duas colunas) não têm representação no contrato.

**Impacto.** Limitação coerente com o escopo declarado (candidatos entre tabelas; V0.3 é que
prevê relacionamentos), mas o relatório não informa que a tabela tem referências internas — o
usuário pode concluir que não há relacionamento algum.

**Correção sugerida.** Manter fora de escopo, mas registrar `INFO` quando duas colunas da mesma
tabela compartilharem a dica de identificador e houver sobreposição de valores — sem criar
candidato. Documentar explicitamente em `docs/DATA_CONTRACTS.md`.

## 5. Controles que resistiram (o que está certo)

Estes pontos foram atacados de propósito e **não** cederam. São evidência de que a disciplina do
contrato não é apenas discurso.

| Propriedade | Ataque aplicado | Resultado |
|---|---|---|
| Nenhum valor de célula nas saídas | marcador único `SEGREDO_NAO_DEVE_VAZAR_9F2` em célula de texto e em `Observação`; varredura dos 4 artefatos e de `json_text` | marcador ausente em todos (`test_no_cell_value_reaches_any_artifact`) |
| Determinismo | duas execuções do mesmo arquivo, mesma locale → `json_text` comparado byte a byte | idêntico (`test_analysis_is_deterministic`) |
| Fonte preservada | SHA-256 de 64 chars, `source_integrity.unchanged=True`, sem `source_changed_during_analysis` | preservado (`test_source_integrity_is_recorded`) |
| Nada é executado | `plan.json` com `executed=false` em todas as transformações; fórmulas XLSX → `None` + `formula_not_evaluated` BLOCKER | não executa (`test_artifacts_are_complete_json_and_markdown`, `test_formulas_are_never_evaluated`) |
| Contrato de ocorrência | 25 linhas ruins: severidade, escopo, `count`, `source_rows` ≤ 20, `rows_truncated` coerente | cumpre (`test_issue_contract_shape_and_row_evidence_cap`) |
| Fail-closed em moeda | valor sem coluna de moeda, moeda desconhecida, símbolo divergente do código | nenhum valor monetário é exposto; BLOCKER com linhas |
| Ambiguidade não é adivinhada | `1/2/2026`, `1.234` sem locale, `0,500` sem locale | `ambiguous`, nunca um valor escolhido |
| Semântica é hipótese | 100 % dos valores reconhecidos + nome exato | sugestão `status='hypothesis'`, `semantic_validation=not_performed` sempre |
| Duplicata não é removida | linhas idênticas legítimas | `suspected_duplicates` WARNING, `profile.duplicate_rows=1`, `rows` ainda 2 (`test_duplicate_rows_are_flagged_and_never_removed`) |
| Cabeçalho degradado | `ID;ID;;Valor` e planilha esparsa com célula em C5 | nomes desambiguados (`ID__2`, `column_3`), `duplicate_header`/`blank_header` WARNING, linhagem preservada |
| Codificação | UTF-16/NUL, cp1252, BOM, `--encoding` errado | NUL recusado, cp1252 com WARNING `encoding_fallback`, BOM removido, encoding explícito errado nunca é silencioso |
| Excel multi-aba | aba oculta + aba vazia + `--sheet` inexistente + `header_row` além dos dados | 3 tabelas com IDs estáveis, `InputError` para aba inexistente, zero linhas sem exceção |
| Duplicidade de fonte | mesmo arquivo duas vezes | `InputError('Fonte/aba repetida…')` |
| CLI | exit 0/1/2, recusa de sobrescrita, entrada ausente | `0` análise, `1` artefato existente/entrada inválida, `2` com `--fail-on-blocker`; sem traceback |
| Reconciliação | troca de célula com total preservado; reordenação; perda de linha; renome de coluna; hash divergente | `unapproved_cell_changes`, reordenação aprovada, `row_loss_or_gain`, `schema_changed`, `source_changed` |
| Precisão decimal | totais com 30 dígitos e centavos que somem em `float` | strings decimais exatas e `Decimal` com contexto ampliado; coberto em `test_reorder_with_lineage_is_exact_even_with_cancelling_large_values` e `test_large_decimal_totals_preserve_cents_beyond_context_precision` (suíte oficial) e em `test_identical_tables_pass_and_totals_are_decimal_strings` (aqui) |
| Limite de evidência na reconciliação | 120 células alteradas | `changes` com 100 itens + `changes_truncated=True` |

## 6. Lacunas desta auditoria

Declarado para não confundir "verde" com "validado":

1. **Sem bases reais.** Todos os dados são sintéticos. Nenhuma conclusão aqui autoriza tratar
   dados de cliente como validados; a própria saída do produto diz `semantic_validation=not_performed`.
2. **Sem Power BI Desktop, sem PBIR/DAX.** Fora do escopo V0.2 (o motor declara
   `Analytical: not_implemented`); nenhuma verificação visual foi feita nem alegada.
3. **Sem teste de escala.** Só arquivos pequenos (≤ 60 linhas). Complexidade, tempo e memória em
   10⁵–10⁶ linhas, workbooks com dezenas de abas e planilhas com 16 384 colunas não foram medidos.
   `profile_table` percorre coluna a coluna em Python, o que sugere custo linear com fator alto —
   hipótese, não medição.
4. **Fuzz limitado.** Cotação CSV (aspas não fechadas, `\r` isolado, escapes), ZIP malformado,
   _zip bomb_ e XML hostil não foram fuzzed; só os caminhos de erro cobertos pelos testes acima.
5. **Só pt-BR/en-US.** Outras locales (espanhol, francês) caem em `ambiguous` por desenho; não
   avaliei se a mensagem explica isso ao usuário.
6. **Concorrência.** Duas execuções simultâneas no mesmo diretório de saída não foram testadas;
   o contrato promete substituição atômica por arquivo, não transação.
7. **Plataforma.** Somente Windows. Diferenças de filesystem (case sensitivity, links) não foram
   exercitadas além do que a suíte oficial já cobre.
8. **`reconcile` é API-only.** A CLI não executa reconciliação (documentado no README); não há
   caminho de usuário final para esse controle hoje.

## 7. Recomendações priorizadas

Ordem = risco de bloquear um arquivo correto ou de produzir número errado em uso real, não esforço.

### P0 — antes de qualquer uso com dados de terceiros

1. **Exigir evidência de valores no fallback por nome** (QA-F01). `named()` em `financial.py`
   deve recusar a coluna quando `map_columns` já a classificou como `insufficient_evidence`;
   sem isso, `Tipo`/`Status` de domínio não financeiro (estoque, RH, logística) geram BLOCKER por
   linha. Alternativa: só promover por nome se o mapeamento não tiver opinião contrária, e nunca
   quando a taxa de tokens reconhecidos for 0 %.
2. **Normalizar nomes compostos** (QA-F03). `Valor Total`, `Data de Pagamento`, `Data de
   Recebimento`, `Vlr. Pgto` precisam ser reconhecidos; hoje `amount` e `payment_date` ficam vazios e
   o arquivo limpo é reprovado com mensagem falsa. Manter o requisito de evidência de valores e
   cobrir com teste negativo (`Total de Itens`, `Data de Cadastro`).
3. **Não usar a vírgula como delimitador de um arquivo de coluna única** (QA-F16). Validar a
   contagem de campos por candidato antes de recusar; no mínimo, tratar 1 campo no cabeçalho +
   N>1 constante no corpo como coluna única com `INFO`, em vez de `InputError`.
4. **Registrar a decisão de severidade do P0** em `docs/DATA_CONTRACTS.md`: por que BLOCKER por
   linha em coluna não reconhecida é `blocked` e não `review_required`. Um veredito que bloqueia
   dados íntegros é tão caro quanto um que aprova dados ruins.

### P1 — próxima iteração

5. **Filtrar abas não tabulares** (QA-F05) e restringir o `except` de leitura a
   `InvalidFileException`; erro interno inesperado não pode virar "arquivo corrompido".
6. **Simetrizar `multiplication_risk`** (QA-F04): avaliar nulos dos dois lados do par candidato,
   com o mesmo limiar, e documentar a regra. A assimetria produz BLOCKER em uma direção e silêncio
   na outra para o mesmo par.
7. **Restringir `status` genérico** (QA-F08b): coluna chamada apenas `Status` com valores `0/1` é
   indicador binário, não situação de pagamento; exigir tokens de pagamento ou vocabulário
   `Pago/Pendente/Cancelado` antes de atribuir o papel.

### P2 — robustez de vocabulário e de layout

8. **Ampliar vocabulário de status/movimento** (QA-F08): `Em aberto`, `Aguardando`, `Parcial`,
   `Baixado`, `Liquidado`, `Recebimento`, `Pagamento`, `Devolução`. Cada adição precisa de teste de
   regressão e de reavaliação do efeito no `blocked_scope`.
9. **Detectar linha de total/rodapé** (QA-F14): marcar WARNING quando a última linha tem rótulo de
   total ou quando um rodapé irregular aparece, em vez de ingerir como registro ou recusar o arquivo
   inteiro. Nunca remover sem aprovação — apenas sinalizar.
10. **Tratar separador de milhar ambíguo com política explícita** (QA-F09): `0,500` sob `en-US` e
    `0.500` sob `pt-BR` devem ir para `ambiguous` (ou exigir confirmação de escala), porque hoje o
    valor é magnificado 1000× sem aviso.

### P3 — evolução de contrato

11. **Pares intra-tabela e chave composta** (QA-F15): documentar a limitação como decisão de V0.2 e
    planejar detecção de `*_ID` na mesma tabela como candidato de dimensão degenerada.
12. **Expor reconciliação na CLI** (`reconcile` hoje é API-only), com política de aprovação de
    mudanças por artefato, para que o controle exista no fluxo do usuário final.
13. **Medir escala** antes de prometer desempenho: perfil de tempo/memória em 10⁵–10⁶ linhas e em
    workbooks com dezenas de abas; hoje só há hipótese de custo linear.

Nenhuma dessas correções foi implementada por esta auditoria: o escopo foi medir e documentar. As 7
regressões marcadas `expectedFailure` já falham hoje e passam a passar quando cada correção for
aplicada — remova o decorador no mesmo commit da correção.

## 8. Índice de reprodução

Cada achado tem um teste nomeado. Para ver a falha isolada, rode o arquivo inteiro e filtre pelo
nome:

```
python -m unittest discover -s tests/qa_external -p "test_qa_financial.py" -v
python -m unittest discover -s tests/qa_external -v      # todos os 79 (7 xfail)
```

| Achado | Arquivo::teste |
|---|---|
| QA-F01 | `tests/qa_external/test_qa_financial.py` — `test_qa_f01_*` (2 casos) |
| QA-F03 | `tests/qa_external/test_qa_financial.py` — `test_qa_f03_*` |
| QA-F16 | `tests/qa_external/test_qa_intake.py` — `test_single_column_csv_with_decimal_comma_is_rejected` |
| QA-F05 | `tests/qa_external/test_qa_intake.py` — `test_qa_f05_chartsheet_must_not_hide_the_data_sheets` |
| QA-F04 | `tests/qa_external/test_qa_relationships.py` — `test_qa_f04_*` |
| QA-F08b | `tests/qa_external/test_qa_financial.py` — `test_qa_f08b_*` |
| QA-F09 | `tests/qa_external/test_qa_parsing.py` — `test_qa_f09_*` |
| QA-F08 | `tests/qa_external/test_qa_financial.py` — `test_unknown_status_blocks_cash_metrics_with_row_evidence` |
| QA-F14 | `tests/qa_external/test_qa_intake.py` — `test_footer_total_row_is_ingested_as_a_regular_record` |
| QA-F15 | `tests/qa_external/test_qa_relationships.py` — `test_intra_table_column_pairs_are_never_candidates` |
| QA-F02 (controle) | `tests/qa_external/test_qa_financial.py` — `test_qa_f02_*` |
| Controles da seção 5 | `test_qa_engine.py`, `test_qa_intake.py`, `test_qa_validation.py` (nomes citados na tabela) |

Como a pasta não tem `__init__.py`, use `discover` (como acima) em vez de importar
`tests.qa_external...` como pacote. Nenhum teste lê fixture do repositório, nenhum escreve fora do
diretório temporário e nenhum imprime valor de célula; `python -m unittest discover -s tests`
continua com 53 testes porque a pasta não é coletada.

## 9. Conclusão

O V0.2 faz o que o contrato promete no que é mais difícil: não adivinha, não esconde valor de
célula, não executa conteúdo, preserva o arquivo e mantém a semântica como hipótese explícita. O
rigor de saída, porém, está calibrado para um vocabulário e um layout que o intake ainda não
reconhece com segurança. O resultado prático é que **arquivos corretos, comuns em pt-BR, são
bloqueados por motivos que não estão nos dados** — e um veredito assim corrói a confiança mais
rápido do que uma lacuna declarada.

Enquanto QA-F01, QA-F03 e QA-F16 não forem corrigidos, o uso recomendado é: dados sintéticos ou
internos, operador que saiba ler `issues` e reconhecer mensagem falsa, e nenhuma decisão de negócio
tomada a partir do veredito. Depois dos P0, os P1 (chartsheet, `multiplication_risk`, `Status`
binário) determinam se a ferramenta pode rodar sem supervisão em lote.

**Veredito: aprovado com restrições — não recomendado para uso real sem as correções P0.**
