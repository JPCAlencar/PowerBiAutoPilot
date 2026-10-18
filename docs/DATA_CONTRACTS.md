# Contratos de dados V0.2.0

## Entrada e preservação

`read_source(path, ReadOptions(sheet=None, sep=None, encoding=None, header_row=1)) -> list[Table]`.

Formatos: CSV textual, XLSX e XLSM. XLSM é tratado como planilha de dados, nunca executado. XLS/PBIX/SQL e outros formatos são recusados. Arquivos corrompidos/protegidos retornam InputError com mensagem sem valores de células. A leitura mantém o conteúdo original no disco e calcula SHA-256 dos bytes.

CSV: UTF-8/UTF-8 BOM por padrão; fallback cp1252 é hipótese com WARNING, não detecção comprovada. Outras codificações exigem opção explícita; NUL não é aceito. Delimitadores detectáveis: vírgula, ponto e vírgula, tab, pipe; `--sep` aceita um caractere. Linhas com quantidade de campos divergente falham, nunca são descartadas. Somente célula vazia é convertida em None; `NA`, `NULL` e códigos com zeros à esquerda ficam como texto. Linha vazia física vira registro vazio preservado. `header_row` em CSV conta registros lógicos, e em Excel conta linhas da planilha; para CSV multilinha, o número de origem é a linha física final do registro.

Excel: todas as abas por padrão, inclusive ocultas; seleção por nome exato. Nenhuma fórmula é avaliada nem seu cache é usado. Células de fórmula ficam indisponíveis (None) e geram BLOCKER com referência de origem, inclusive no cabeçalho. Campos armazenados como números permanecem numéricos: formatação visual e zeros apenas de máscara não são reconstruídos. Linhas vazias no intervalo usado da planilha são preservadas; formatação residual pode ampliar esse intervalo.

Cabeçalhos vazios recebem `column_N`; nomes repetidos recebem `__2`, `__3`, evitando colisões. O mapeamento posicional `source.headers` preserva o nome original. Nomes de fórmula não são incluídos. Não é inferido automaticamente que uma linha de preâmbulo seja cabeçalho: informe `header_row`.

`Table` interno:

| Campo | Tipo | Contrato |
|---|---|---|
| `id` | string | prefixo de 16 caracteres SHA-256 + `:` + aba ou csv |
| `frame` | pandas.DataFrame | dados lidos, não serializados como amostras |
| `source` | objeto | file (somente nome), sha256, format, sheet ou null, header_row, headers; encoding/delimiter para CSV |
| `row_numbers` | list[int] | identidade de origem alinhada à posição do DataFrame |
| `issues` | list[Issue] | diagnósticos da ingestão |

O mesmo conteúdo/aba não pode entrar duas vezes em uma análise. A granularidade de negócio não é definida por esse identificador técnico.

## Parsers escalares

`number(value, locale=None)` e `date(value, locale=None)` retornam Parsed(value, status). Status é `valid`, `missing`, `invalid` ou `ambiguous`; somente valid tem valor. Valores numéricos usam Decimal; datas usam datetime.date. Booleanos e números seriais não são datas. Datas ISO são inequívocas; formatos com dia/mês ambos possíveis permanecem ambíguos sem locale (exceto quando são iguais). Anos com dois dígitos não são suportados.

pt-BR: agrupamento ponto, decimal vírgula, dia/mês. en-US: agrupamento vírgula, decimal ponto, mês/dia. Sem locale, números com ambos separadores e agrupamentos válidos são reconhecidos; um único separador seguido de três dígitos é ambíguo. Parênteses representam negativos. Texto monetário aceita R$, US$, BRL, USD, EUR, $, €; um `$` isolado não comprova USD. Notação científica textual, percentuais e agrupamentos com espaços não são suportados. Nenhuma conversão muda a fonte ou define natureza financeira.

## Esquema JSON

Todos os JSONs possuem `schema_version: "0.2.0"`. Valores monetários/estatísticas Decimal são strings, nunca float; não há NaN/Infinity. Campos desconhecidos são null ou status explícito. Consumidores devem verificar a versão e nunca interpretar ausência de BLOCKER como validação de semântica.

Raiz `analysis.json`:

| Campo | Tipo | Significado |
|---|---|---|
| `engine_version`, `schema_version` | string | versão do produtor e do contrato |
| `locale` | string ou null | regra regional explicitada |
| `stages` | objeto | Raw preserved, Clean planned_only, Analytical not_implemented |
| `tables` | list[TableReport] | resultados por tabela |
| `relationships` | objeto | candidates, examined_pairs, truncated, limit |
| `issues` | list[Issue] | conjunto de ocorrências de fontes, perfis, domínios e relações |
| `validation` | ValidationSummary | status técnico e escopos bloqueados |
| `source_integrity` | lista | hash por arquivo e comparação ao fim da leitura |
| `limitations` | list[string] | limites da análise executada |

TableReport contém `id`, `profile`, `semantics`, `financial`, `transformations`, `validation`.

Profile: `table`, `source`, `rows`, `columns`, `duplicate_rows`, `empty_rows`, `grain`, `issues`. Cada coluna tem name, storage_type, type sugerido (text/number/date/boolean), missing_count/percent, fill_percent, distinct_count, candidate_key, number_parse/date_parse (contagens por status), number_distribution ou null, date_range ou null. Boolean é reconhecido para valores nativos; textos de status são tratados como evidência semântica separada. Distribuição numérica tem min/max/median strings e contagens negative/zero/iqr_outlier. IQR é um detector exploratório, não prova de erro. candidate_key exige todos preenchidos e únicos; não valida chave composta nem entidade.

Semantics é lista por coluna: `column`, `status` (hypothesis ou insufficient_evidence), `suggestions`. Sugestão contém role, confidence, confidence_kind, evidence, evidence_kind=inference, requires_business_contract=true. Evidências incluem quantidade não nula, compatibilidade e razão plausível. Força de 0.5/0.6/0.7/0.85 é heurística: compatibilidade parcial, campo genérico, amostra pequena ou maior compatibilidade. Não é probabilidade empírica nem grau de validação. Até compatibilidade total pode representar outro processo.

Financial: `table`, `domain` (name, status, reason), `roles` (papel → nomes de colunas), currencies_observed, indicators, issues, unknowns. Uma sugestão de domínio financeiro não é fato observado. Indicador: id, meaning, status (`available` para contagem de linhas; `requires_contract` ou `insufficient_evidence` para os demais), missing_requirements e evidence_kind. Não há resultados monetários calculados.

RelationshipCandidate: from_table/column, to_table/column, cardinality (`one_to_one`, `one_to_many`, `many_to_one`, `many_to_many`), coverage_percent (linhas de origem não nulas com correspondência), orphan_rows, null_source/target_rows, matched_join_rows (estimativa de correspondências não nulas), multiplication_risk, null_join_policy, validated=false, status=candidate_requires_review, evidence_kind=inference e reason. Identificadores iguais podem ser entidades distintas. Não aplicar joins usando esses resultados sem revisão. Ambas as direções podem aparecer; risco na direção inversa não proíbe usar uma dimensão única no sentido apropriado.

`profile.json` contém schema_version e tables (somente perfis). `plan.json` contém schema_version, executed=false e tables com table, transformations e indicators. `report.md` resume o JSON com limites de 50 colunas/hipóteses por tabela, 30 relações e 100 ocorrências; limites são indicados no texto. JSON conserva todas as ocorrências, mas referências de linhas são limitadas.

## Ocorrências e evidência

Issue: code (identificador estável), severity (`BLOCKER|WARNING|INFO`), table, column ou null, message, count, source_rows (até 20), rows_truncated, scope e evidence_kind. Observação de valores, contagens e falhas é `observed`; papéis/relações são `inference`; indicadores ainda não confirmados são `hypothesis`; grão e contratos ausentes são `unknown` por status/campo. A regra de qualidade é aplicada deterministicamente, mas sua interpretação pode requerer revisão.

BLOCKER impede a operação identificada pelo escopo, não todas as análises. WARNING merece revisão e nunca autoriza correção automática. INFO registra limitações ou oportunidade. Códigos principais: invalid/ambiguous_number/date, missing_values, suspected_duplicates, empty_rows/table, formula_not_evaluated, unknown/mixed_currency, currency_conflict, unknown_movement_type, unknown_payment_status, paid_without_payment_date, special_movements, cancelled_records, non_additive_balance, classification_variants, join_multiplication_risk, candidate_orphans e insufficient_schedule_dates.

ValidationSummary: counts por severidade, blocked_scopes, status (`blocked_scopes`, `review_required`, `no_findings_in_supported_checks`), semantic_validation=not_performed, transformations_executed=false. Não existe status global “dados validados”.

## Contrato de medidas e planejamento

Antes de construir uma medida, confirmar grão e entidade, classificação de natureza, convenção de sinais, papel temporal, moeda e conversão, regras de status/cancelamentos/transferências/estornos, agregação e tratamento de nulos/duplicatas. Receita prevista, recebida, despesa incorrida, paga e saldo têm definições separadas. Inadimplência exige data de referência e política, além de vencimento/status. O motor não usa relógio atual para supor atraso.

TransformationStep: id, source e destination (stage/table/column), operation, reason, risks, preconditions, status=proposed_requires_review, executed=false. Operações atuais: resolve_locale, parse_number/date, review_missing, review_duplicates, confirm_semantics. Nenhuma exclusão/imputação/correção é executada. Não há CLI para aprovar um plano nesta versão.

## Reconciliação independente

`reconcile(before: Table, after: Table, amount_columns=(), currency_column=None, locale=None)` retorna status passed/failed, rows_before/after, changed_cells, changes (source_row/column, até 100), changes_truncated, totals e issues. Não inclui valores de células na trilha; as referências permitem auditoria local.

Compara contagem/identidade de linhas, unicidade da linhagem, esquema, hash da origem e células alinhadas por identidade. Células alteradas falham, mesmo que o total se mantenha. Reordenação com identidade preservada é permitida. Totais de amount_columns exigem coluna de moeda explícita e valores válidos, sem ambiguidade. Totais por moeda têm before/after/delta como strings decimais. Moedas suportadas nesta etapa: BRL, USD, EUR, GBP, ARS, JPY, CAD, CHF, AUD; códigos adicionais precisam de extensão explícita. Conflitos entre símbolo/código no valor e coluna são bloqueados.

Uma passagem comprova apenas as verificações solicitadas. Chamar sem amount_columns não verifica totais. A CLI não invoca reconciliação entre estágios porque não transforma dados; verifica apenas preservação das fontes. Mudanças legítimas de formato também falham na API estrita até existir contrato de transformação na V0.3.
