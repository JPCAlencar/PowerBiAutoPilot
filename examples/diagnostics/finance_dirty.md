# Diagnóstico PowerBI Autopilot V0.2

Estado técnico: **blocked_scopes**. Semântica de negócio: **não validada**.

Ocorrências: BLOCKER: 5, WARNING: 3, INFO: 0.

Os arquivos originais são preservados. Clean e Analytical não foram produzidos. Nenhuma correção foi executada.

## Fonte: finance_dirty.csv / CSV

Linhas: 9; duplicatas suspeitas: 1. Granularidade: **desconhecida**.

SHA-256: `958fca5f6305c01ab9d8610a4cfa03dc3b2b6763784ce7b9557af535ce1f3c76`.

| Coluna | Tipo sugerido | Preenchimento | Distintos | Chave candidata |
|---|---|---:|---:|---|
| ID | text | 100.0% | 8 | False |
| Tipo | text | 100.0% | 2 | False |
| Valor | number | 100.0% | 8 | False |
| Moeda | text | 100.0% | 2 | False |
| Pago | text | 100.0% | 3 | False |
| Data Lançamento | date | 100.0% | 8 | False |
| Competência | date | 100.0% | 2 | False |
| Data Vencimento | date | 100.0% | 5 | False |
| Data Pagamento | date | 66.67% | 4 | False |
| Categoria | text | 100.0% | 4 | False |
| Cliente_ID | text | 100.0% | 3 | False |

### Hipóteses semânticas

- ID: entity_id (força 0.6).
- Tipo: movement_type (força 0.85).
- Valor: amount (força 0.5).
- Moeda: currency (força 0.85).
- Pago: payment_status (força 0.5).
- Data Lançamento: posting_date (força 0.5).
- Competência: competence_date (força 0.85).
- Data Vencimento: due_date (força 0.85).
- Data Pagamento: payment_date (força 0.85).
- Categoria: category (força 0.6).
- Cliente_ID: entity_id (força 0.6).

Força heurística combina padrão de nome e valores compatíveis; não representa probabilidade.

### Indicadores e dependências

| Indicador | Estado | Informações adicionais |
|---|---|---|
| record_count | available | contagem de linhas observada |
| cash_received | insufficient_evidence | amount, payment_status, payment_date |
| cash_paid | insufficient_evidence | amount, payment_status, payment_date |
| incurred_expenses | insufficient_evidence | amount |
| expected_receipts | insufficient_evidence | amount, forecast_policy |
| cash_balance | insufficient_evidence | amount, payment_date, opening_balance |
| overdue | insufficient_evidence | amount, payment_status, overdue_policy, reference_date |

Plano: 18 operações propostas, nenhuma executada. Detalhes em plan.json.

## Relacionamentos candidatos

São hipóteses; nenhum join foi executado. Valores nulos exigem política explícita.


## Ocorrências

| Severidade | Código | Explicação | Escopo | Contagem | Linhas de origem (até 20) |
|---|---|---|---|---:|---|
| BLOCKER | invalid_number | Conversão exige correção na origem ou regra regional explícita. | 958fca5f6305c01a:csv.Valor | 1 | [3] |
| BLOCKER | invalid_date | Conversão exige correção na origem ou regra regional explícita. | 958fca5f6305c01a:csv.Data Lançamento | 1 | [6] |
| WARNING | missing_values | Células ausentes ou em branco. | 958fca5f6305c01a:csv.Data Pagamento | 3 | [2, 4, 5] |
| WARNING | suspected_duplicates | Linhas iguais podem ser transações legítimas; nenhuma removida. | 958fca5f6305c01a:csv | 1 | [10] |
| BLOCKER | unknown_payment_status | Status ausente ou não reconhecido; não presumir pago/pendente. | cash_metrics | 1 | [5] |
| BLOCKER | paid_without_payment_date | Pagamento declarado sem data de pagamento utilizável. | cash_metrics | 1 | [2] |
| BLOCKER | mixed_currencies | Múltiplas moedas: agrupar por moeda; conversão exige taxa e data contratadas. | cross_currency_metrics | 2 | [] |
| WARNING | classification_variants | Categorias diferem apenas em espaços, acentos ou caixa; equivalência precisa de revisão. | 958fca5f6305c01a:csv.Categoria | 4 | [2, 4, 6, 8] |

## Limitações

- Sem confirmação automática de semântica ou granularidade.
- Sem execução de transformações; reconciliação entre estágios não executada.
- Sem indicadores financeiros calculados, DAX, PBIP ou inspeção visual.
- Análise integral em memória; sem amostragem ou streaming.
- Confiança heurística não é probabilidade calibrada.
