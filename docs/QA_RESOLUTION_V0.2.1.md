# Resolução do QA independente — V0.2.1

Data: 2026-10-18. Escopo: estabilização offline da V0.2, sem execução de
transformações, autoria Power BI ou commits automáticos.

## Investigação e plano de execução

Leitura: relatório independente integral, sete arquivos com os 79 testes externos,
README, arquitetura, contratos, visão e roadmap. Baseline reproduzido:
53 testes originais aprovados; 79 externos aprovados com 7 expected failures.

Plano de correção, com regressões antes de cada alteração:

- [x] QA-F09: unificar validação de agrupamentos numéricos e recusar grupo inicial
  com zero; verificar perfil, diagnóstico e reconciliação nos dois locales.
- [x] QA-F01/F03/F08b/F08/F02: compartilhar reconhecimento controlado de nomes e
  vocabulário contextual; separar hipótese semântica de auditoria de campos
  incompletos, mantendo bloqueios para datas/status financeiros não utilizáveis.
- [x] QA-F16/F05: resolver coluna única pelo cabeçalho lógico, preservar cotação e
  linhas; investigar chartsheets na dependência instalada antes de corrigir.
- [x] QA-F04/F14: restringir multiplicação às correspondências não nulas e
  diagnosticar possíveis totais sem excluir registros ou confirmar grão.
- [x] Executar as duas suítes completas e CLI relevante; revisar diff e registrar
  decisões por achado, resultados reais e limitações.

Decisões: não converter estados parciais/administrativos em pagamento concluído;
não aceitar rodapés irregulares descartando campos. O delimitador anulável exigiu
versionamento explícito de **engine e schema para 0.2.1**, com migração em
DATA_CONTRACTS.md. Relações intra-tabela e chaves compostas continuam fora da
estabilização. Não foram adicionadas dependências ou integrações externas.

## Decisões por achado

| Achado | Investigação e decisão | Implementação | Evidência |
|---|---|---|---|
| QA-F01 — P0 | Confirmado: fallback incondicional ignorava recusa semântica e bloqueava tarefas/cadastros. Remover toda auditoria por nome ocultaria estados financeiros inválidos; essa sugestão não foi adotada. | `financial.audit_column` não promove papéis, exige contexto financeiro para fallback de Tipo/Status e recusa escolha entre múltiplas candidatas. Meta numérica isolada não é contexto financeiro. | Os dois `test_qa_f01_*` passam sem marcador; `test_numeric_task_targets_do_not_activate_financial_status_audit`, `test_financial_unknown_fields_still_block_without_becoming_roles`. |
| QA-F02 — controle | Não é defeito: pagamento declarado com data inválida precisa continuar bloqueado, mesmo quando o mapper recusa a data. | Auditoria de datas rejeitadas preservada, usando o mesmo reconhecimento de cabeçalhos; nenhum rebaixamento de severidade. | `test_qa_f02_known_alias_with_invalid_value_is_still_blocked`, `test_invalid_compound_payment_date_still_blocks`. |
| QA-F03 — P0 | Confirmado: nomes compostos usuais não correspondiam aos aliases. Contenção livre de tokens sugerida pelo auditor poderia interpretar nomes enganosos. | Comparação integral/sufixo de alias com remoção de conectivos; aliases compostos explícitos. Mantém compatibilidade mínima de valores de 80%, hipótese e confiança heurística. | `test_qa_f03_realistic_pt_br_headers_are_mapped` sem marcador; `test_compound_headers_require_values_and_do_not_match_unrelated_names` cobre aliases, valores inválidos, Total de Itens e Data de Cadastro. |
| QA-F04 — P1 | Confirmada a parcela de nulos que criava risco falso. A afirmação do relatório de que todo risco deveria ser simétrico é incorreta: multiplicação real depende da direção. Nulos tampouco são órfãos no código atual. | Risco depende só de `matched_join_rows > linhas de origem não nulas com correspondência`. Contagens de nulos e política indefinida preservadas. Não se presume que qualquer executor exclua nulos do join. | `test_qa_f04_null_multiplication_risk_is_symmetric` sem marcador; testes novos de ordem dos arquivos e de many-to-one sem multiplicação versus one-to-many com multiplicação. |
| QA-F05 — P1 | Confirmado, com causa adicional: no openpyxl 3.1.5 instalado, chartsheet vazia já falhava em `read_chartsheet` com AttributeError durante o carregamento. Filtrar abas depois de `load_workbook` seria insuficiente. | Adaptador local de ExcelReader ignora chartsheets antes do carregamento de desenhos, emite INFO e mantém fórmulas indisponíveis. Seleção não tabular e workbook sem tabela têm erro específico. Falhas internas inesperadas recebem mensagem sanitizada distinta de arquivo inválido. | `test_qa_f05_chartsheet_must_not_hide_the_data_sheets` sem marcador; `test_chartsheets_with_and_without_drawings_do_not_hide_data`, `test_chart_only_workbook_is_refused_as_non_tabular`; checks de bytes e fórmulas. |
| QA-F08 — P2 | Lacuna parcialmente confirmada. “Em aberto” é sinônimo inequívoco de pendência. “Parcial”, “Baixado”, “Aguardando” e estados administrativos não estabelecem pagamento concluído; ampliação indiscriminada recusada. | Acrescentados `em_aberto` e `quitado`; vocabulário e distinção de flags publicados nos contratos. Estados não contratados continuam desconhecidos; `vencido` não calcula inadimplência nem perde valor original. | Teste externo atualizado para `test_em_aberto_is_pending_without_false_cash_blocker`; novos testes de estados desconhecidos e ausência de política de atraso. |
| QA-F08b — P1 | Confirmado: 1/0, booleanos e Sim/Não em Status genérico não comprovam pagamento. A revisão também encontrou inversão em “Não Pago”. | Flags só entram no vocabulário sob nome positivo exato normalizado (`Pago/Paid/Quitado/Liquidado`). Flags genéricas/qualificadas não promovem papel. Colunas mistas não transformam flag desconhecida em pago. | `test_qa_f08b_numeric_flag_is_not_a_payment_status` sem marcador; testes com texto, números, booleanos, polaridade negativa, mistura e compatibilidade da coluna Pago. |
| QA-F09 — prioridade financeira elevada | Defeito confirmado de magnitude, além da classificação “provável” do auditor. O parser devolvia 500 para uma representação de fração no locale oposto; o perfil publicava 500 e reconcile entre cópias idênticas retornava passed. | Uma gramática para todos os caminhos de agrupamento exige primeiro grupo não zero. Recusa grupos iniciais zero/zero à esquerda nos dois locales, também com moeda, sinal, múltiplos grupos e formatos mistos sem locale. Não tenta adivinhar o locale oposto. | `test_qa_f09_leading_zero_group_must_not_be_a_thousands_separator` sem marcador e quatro regressões MagnitudeTests; perfil sem distribuição válida e reconciliação failed, sem total monetário para a entrada recusada. |
| QA-F14 — prioridade de grão | Risco confirmado: total alinhado passava silenciosamente como detalhe. A ingestão deve preservar Raw; excluir a linha seria um novo defeito. Rodapé irregular continua incompatível com contrato de quantidade de campos. | Profiling sinaliza possíveis totais/subtotais em qualquer posição como WARNING/inference com evidência limitada. Estatísticas continuam incluindo todas as linhas. Métricas exigem `detail_row_policy`; plano propõe `review_aggregate_rows`, sem exclusão ou execução. | Teste externo atualizado para `test_footer_total_row_is_preserved_and_flagged_by_profiling`; quatro AggregateRowTests cobrem CSV/XLSX, subtotais intermediários, limites de evidência, negativos, grão desconhecido e preservação. |
| QA-F15 — P3 | Limitação confirmada e coerente com V0.2. Pares intra-tabela/chaves compostas não foram implementados. INFO baseado apenas em sobreposição não comprovaria autorreferência. | Limitação explicitada nos contratos e no campo `analysis.limitations`; busca continua restrita a tabelas distintas e nomes de identificador iguais. | `test_intra_table_column_pairs_are_never_candidates` preservado; nenhum relacionamento fabricado. |
| QA-F16 — P0 | Confirmado: o sniffer escolhia vírgula do corpo mesmo sem separador no cabeçalho. Não se deve mascarar CSV realmente irregular tentando sempre uma coluna. | Autodetecção usa cabeçalho lógico, cotação e consistência de campos. Sem separador estrutural, preserva coluna única como hipótese INFO e delimiter null. `--sep` continua impondo a forma. | Teste externo atualizado para `test_single_column_csv_with_decimal_comma_is_preserved`; regressões de decimal, aspas, linha vazia, multilinha, header_row lógico, bytes e recusa de múltiplos campos irregulares. |

QA-F06, QA-F07 e QA-F10 a QA-F13 não têm achados independentes no relatório;
foram absorvidos na triagem do auditor. Não foram inventadas resoluções separadas.

## Regressões e revisão

Os sete cenários marcados expectedFailure foram reproduzidos antes das correções.
Todos os sete marcadores foram removidos após tratar suas causas (QA-F01 ×2,
F03, F04, F05, F08b e F09). Nenhum teste foi excluído. A suíte externa conserva
79 métodos; três métodos que descreviam comportamento defeituoso (F08, F14, F16)
tiveram nome/expectativas atualizados para o contrato corrigido.

`tests/test_stabilization.py` acrescenta 27 testes, com cenários sintéticos e
expectativas independentes. Regressões de defeitos novos foram vistas falhando
antes da alteração de produção; controles negativos e compatibilidade também
foram executados. A suíte original mantém seus 53 métodos; a única expectativa
alterada é a versão JSON exata em `test_cli`, agora 0.2.1, correspondente à migração
documentada. Validações monetárias, de identidade e severidades não foram
relaxadas para aprovar os testes.

Uma revisão de código separada, somente leitura, encontrou dois casos adicionais:
Meta numérica isolada ativando fallback de Status/Tipo e sufixo “Não Pago”
invertendo flag. Ambos foram reproduzidos em regressões normais e corrigidos.
O revisor não encontrou outros defeitos concretos nos caminhos inspecionados de
agrupamento, CSV, chartsheets, multiplicação e preservação de totais. Essa revisão
não avaliou bases reais, desempenho, renderização ou a documentação ainda em edição.

A revisão final também verificou a recusa de conversões em cabeçalhos abreviados:
`Vlr. Pgto` e `Dt Pagto` agora mantêm diagnósticos `invalid_number/invalid_date`
quando seus valores são inválidos, além de não receberem papel semântico. A
regressão `test_abbreviated_amount_and_payment_dates_keep_conversion_diagnostics`
falhou antes da correção dos hints de profiling e passou depois.

## Evidência final de validação

Ambiente executado: Windows, CPython 3.14.5, openpyxl 3.1.5, pandas 2.3.3. Fontes
somente sintéticas; nenhuma chamada a serviço ou API de dados.

| Comando | Resultado observado |
|---|---|
| `python -m unittest discover -s tests -p 'test_[bcfi]*.py' -v` | 53 testes originais, OK, exit 0 |
| `python -m unittest discover -s tests -v` | 80 testes (53 originais + 27 regressões), OK, exit 0 |
| `python -m unittest discover -s tests/qa_external -v` | 79 testes independentes, OK, exit 0; zero expected failures, skips ou unexpected successes |

Os 159 testes distintos passaram. A seleção de 53 é uma confirmação separada da
suíte original; não deve ser somada de novo aos 159. Logs locais ignorados pelo
Git: `outputs/qa_original_53_final.log`, `outputs/qa_main_final.log`,
`outputs/qa_external_final.log`.

Também foram executados dez cenários reais de CLI com `python -m
powerbi_autopilot.cli analyze`, sempre com asserção de código de saída, JSON e
hash/bytes da fonte. Cada cenário foi repetido com `--overwrite`, comparando
byte a byte os quatro artefatos (20 chamadas ao todo):

| Fonte/cenário sintético | Opção estrita | Exit observado | Verificação específica |
|---|---|---|---|
| `tests/fixtures/finance_clean.csv` | Sim | 0 | Sem bloqueio no financeiro limpo |
| `tests/fixtures/finance_dirty.csv` | Sim | 2 | Diagnóstico entregue com bloqueios preservados |
| `tests/fixtures/finance_related.xlsx` | Não | 0 | Múltiplas tabelas/relacionamentos diagnosticados |
| Cabeçalhos Valor Total / Data de Pagamento | Sim | 0 | Sem falso pagamento sem data |
| CSV Valor com vírgula decimal, uma coluna | Não | 0 | Linhas preservadas e hipótese explícita de delimitador; moeda continua desconhecida |
| Agrupamento `0,500` sob en-US | Sim | 2 | invalid_number; sem escala escolhida |
| Total alinhado ao cabeçalho | Não | 0 | Duas linhas preservadas, WARNING de total e detail_row_policy em métricas |
| Cadastro Tipo PF/PJ, Status Ativo/Inativo | Sim | 0 | Sem BLOCKER financeiro por nome |
| XLSX com chartsheet vazia | Não | 0 | Aba tabular preservada e INFO de aba não tabular |
| Vlr. Pgto / Dt Pagto com conversões inválidas | Sim | 2 | invalid_number e invalid_date preservados |

Nos dez cenários: fontes preservadas e artefatos determinísticos. Resultado
estruturado local: `outputs/qa_cli_results.json`. Um exit 0 sem opção estrita
indica diagnóstico produzido, não validação financeira ou semântica.

## Limitações e decisões mantidas

- Locale explícito errado ainda pode produzir outra interpretação válida para
  agrupamentos normais, como `1,234`; nenhuma heurística garante a intenção da
  origem. A correção F09 recusa agrupamentos com zero, sem generalizar uma garantia
  impossível sobre todos os valores. Valores numéricos já tipados em Excel não
  recuperam precisão/formatação que o produtor não armazenou.
- Totais são hipótese de layout, com vocabulário finito. Rótulos desconhecidos,
  datas/identificadores preenchidos ou ausência de forma numérica podem impedir
  detecção. Um nome legítimo “Total” pode gerar WARNING. Não se confirmou grão,
  relação aritmética do total nem separação de detalhe/agregado. Rodapés irregulares
  continuam recusados integralmente; aceitá-los exigiria contrato de alinhamento.
- Sem separador no cabeçalho, coluna única é hipótese: corpo multicoluna com
  cabeçalho incompleto requer `--sep` explícito. O motor registra essa decisão,
  preserva conteúdo e não descarta campos silenciosamente.
- Estados parciais/administrativos, nomes de flag qualificados e vocabulários
  específicos de ERP precisam de regras/contrato. Não foram convertidos em pago,
  pendente ou receita automaticamente. Papéis/domínio continuam hipóteses.
- Nulos permanecem fora da estimativa de correspondências e não autorizam join;
  diferentes executores podem casá-los. Chaves compostas, nomes distintos e pares
  intra-tabela permanecem fora do diagnóstico atual.
- O adaptador de chartsheets depende da interface ExcelReader do openpyxl e requer
  regressão ao atualizar a dependência. Não foi criado suporte a gráficos ou
  avaliação de fórmulas/macros.
- Memória integral e múltiplas passagens locais de CSV; não houve benchmark de
  escala, fuzzing exaustivo ou validação com dados reais. Reconciliação segue API
  estrita, sem execução de Clean ou comandos novos da V0.3.
- Não houve Power BI Desktop, PBIR, DAX, renderização ou QA visual. Testes verdes
  comprovam os cenários cobertos, sem validar dados de terceiros.

Os P0 confirmados e os riscos prioritários F09/F14 foram tratados nos cenários
cobertos. Pendências são os limites explicitados acima, não falhas esperadas
ocultas. Nenhum commit foi realizado.
