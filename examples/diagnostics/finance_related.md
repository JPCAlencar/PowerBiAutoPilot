# Diagnóstico PowerBI Autopilot V0.2

Estado técnico: **blocked_scopes**. Semântica de negócio: **não validada**.

Ocorrências: BLOCKER: 2, WARNING: 2, INFO: 0.

Os arquivos originais são preservados. Clean e Analytical não foram produzidos. Nenhuma correção foi executada.

## Fonte: finance_related.xlsx / Movimentos

Linhas: 8; duplicatas suspeitas: 0. Granularidade: **desconhecida**.

SHA-256: `4be27874b0dbfc73ea15c28196b7c20651980269c953743530f16f12b13358d8`.

| Coluna | Tipo sugerido | Preenchimento | Distintos | Chave candidata |
|---|---|---:|---:|---|
| ID | text | 100.0% | 8 | True |
| Tipo | text | 100.0% | 2 | False |
| Valor | number | 100.0% | 8 | True |
| Moeda | text | 100.0% | 1 | False |
| Pago | text | 100.0% | 2 | False |
| Data Lançamento | date | 100.0% | 8 | True |
| Competência | date | 100.0% | 2 | False |
| Data Vencimento | date | 100.0% | 5 | False |
| Data Pagamento | date | 75.0% | 5 | False |
| Categoria | text | 100.0% | 3 | False |
| Cliente_ID | text | 100.0% | 3 | False |

### Hipóteses semânticas

- ID: entity_id (força 0.6).
- Tipo: movement_type (força 0.85).
- Valor: amount (força 0.6).
- Moeda: currency (força 0.85).
- Pago: payment_status (força 0.85).
- Data Lançamento: posting_date (força 0.85).
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
| cash_received | requires_contract | revisar contrato de medidas |
| cash_paid | requires_contract | revisar contrato de medidas |
| incurred_expenses | requires_contract | revisar contrato de medidas |
| expected_receipts | insufficient_evidence | forecast_policy |
| cash_balance | insufficient_evidence | opening_balance |
| overdue | insufficient_evidence | overdue_policy, reference_date |

Plano: 17 operações propostas, nenhuma executada. Detalhes em plan.json.

## Fonte: finance_related.xlsx / Clientes

Linhas: 3; duplicatas suspeitas: 0. Granularidade: **desconhecida**.

SHA-256: `4be27874b0dbfc73ea15c28196b7c20651980269c953743530f16f12b13358d8`.

| Coluna | Tipo sugerido | Preenchimento | Distintos | Chave candidata |
|---|---|---:|---:|---|
| Cliente_ID | text | 100.0% | 2 | False |
| Nome | text | 100.0% | 3 | True |

### Hipóteses semânticas

- Cliente_ID: entity_id (força 0.6).
- Nome: evidência insuficiente.

Força heurística combina padrão de nome e valores compatíveis; não representa probabilidade.

### Indicadores e dependências

| Indicador | Estado | Informações adicionais |
|---|---|---|
| record_count | available | contagem de linhas observada |
| cash_received | insufficient_evidence | amount, movement_type, currency, payment_status, payment_date |
| cash_paid | insufficient_evidence | amount, movement_type, currency, payment_status, payment_date |
| incurred_expenses | insufficient_evidence | amount, movement_type, currency, competence_date |
| expected_receipts | insufficient_evidence | amount, movement_type, currency, due_date, forecast_policy |
| cash_balance | insufficient_evidence | amount, currency, payment_date, opening_balance |
| overdue | insufficient_evidence | amount, currency, due_date, payment_status, overdue_policy, reference_date |

Plano: 1 operações propostas, nenhuma executada. Detalhes em plan.json.

## Fonte: finance_related.xlsx / Categorias

Linhas: 1; duplicatas suspeitas: 0. Granularidade: **desconhecida**.

SHA-256: `4be27874b0dbfc73ea15c28196b7c20651980269c953743530f16f12b13358d8`.

| Coluna | Tipo sugerido | Preenchimento | Distintos | Chave candidata |
|---|---|---:|---:|---|
| Categoria_ID | text | 100.0% | 1 | True |
| Categoria | text | 100.0% | 1 | True |

### Hipóteses semânticas

- Categoria_ID: evidência insuficiente.
- Categoria: category (força 0.6).

Força heurística combina padrão de nome e valores compatíveis; não representa probabilidade.

### Indicadores e dependências

| Indicador | Estado | Informações adicionais |
|---|---|---|
| record_count | available | contagem de linhas observada |
| cash_received | insufficient_evidence | amount, movement_type, currency, payment_status, payment_date |
| cash_paid | insufficient_evidence | amount, movement_type, currency, payment_status, payment_date |
| incurred_expenses | insufficient_evidence | amount, movement_type, currency, competence_date |
| expected_receipts | insufficient_evidence | amount, movement_type, currency, due_date, forecast_policy |
| cash_balance | insufficient_evidence | amount, currency, payment_date, opening_balance |
| overdue | insufficient_evidence | amount, currency, due_date, payment_status, overdue_policy, reference_date |

Plano: 1 operações propostas, nenhuma executada. Detalhes em plan.json.

## Relacionamentos candidatos

São hipóteses; nenhum join foi executado. Valores nulos exigem política explícita.

- 4be27874b0dbfc73:Movimentos → 4be27874b0dbfc73:Clientes: Cliente_ID, many_to_many; cobertura 75.0%; órfãos 2; risco de multiplicação True.
- 4be27874b0dbfc73:Clientes → 4be27874b0dbfc73:Movimentos: Cliente_ID, many_to_many; cobertura 100.0%; órfãos 0; risco de multiplicação True.

## Ocorrências

| Severidade | Código | Explicação | Escopo | Contagem | Linhas de origem (até 20) |
|---|---|---|---|---:|---|
| WARNING | missing_values | Células ausentes ou em branco. | 4be27874b0dbfc73:Movimentos.Data Pagamento | 2 | [4, 5] |
| BLOCKER | join_multiplication_risk | Join candidato pode multiplicar registros e valores. | join:4be27874b0dbfc73:Movimentos.Cliente_ID-&gt;4be27874b0dbfc73:Clientes.Cliente_ID | 10 | [] |
| WARNING | candidate_orphans | Chaves sem correspondência no relacionamento candidato; validar se as tabelas se relacionam. | join:4be27874b0dbfc73:Movimentos.Cliente_ID-&gt;4be27874b0dbfc73:Clientes.Cliente_ID | 2 | [] |
| BLOCKER | join_multiplication_risk | Join candidato pode multiplicar registros e valores. | join:4be27874b0dbfc73:Clientes.Cliente_ID-&gt;4be27874b0dbfc73:Movimentos.Cliente_ID | 10 | [] |

## Limitações

- Sem confirmação automática de semântica ou granularidade.
- Sem execução de transformações; reconciliação entre estágios não executada.
- Sem indicadores financeiros calculados, DAX, PBIP ou inspeção visual.
- Análise integral em memória; sem amostragem ou streaming.
- Confiança heurística não é probabilidade calibrada.
