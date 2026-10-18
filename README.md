# PowerBI Autopilot — Data Intelligence Engine V0.2

Motor local para compreender e diagnosticar dados antes de construir relatórios Power BI. Lê CSV/XLSX/XLSM, perfila todas as abas, sugere semântica com evidências, identifica riscos financeiros e de relacionamentos e planeja transformações sem executá-las. Não depende de IA, Desktop, Fabric ou serviços pagos.

## Instalação e execução

Python 3.10+; validado neste desenvolvimento em Windows/Python 3.13. As dependências precisam estar instaladas antes de trabalhar offline.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m powerbi_autopilot.cli analyze tests/fixtures/finance_clean.csv --output outputs/clean
.venv\Scripts\python -m unittest discover -s tests -v
```

Com ambiente Python já preparado, use `python` normalmente. Para ambientes POSIX, o executável do venv é `.venv/bin/python`.

```powershell
python -m powerbi_autopilot.cli analyze tests/fixtures/finance_dirty.csv --output outputs/dirty --fail-on-blocker
python -m powerbi_autopilot.cli analyze tests/fixtures/finance_related.xlsx --output outputs/workbook
python -m powerbi_autopilot.cli analyze tests/fixtures/regional_br.csv --locale pt-BR --output outputs/br
python -m powerbi_autopilot.cli analyze fonte.csv clientes.xlsx --sep ';' --encoding cp1252 --header-row 2 --output outputs/multiple
```

Excel lê todas as abas por padrão, inclusive ocultas. `--sheet 'Nome exato'` restringe a leitura. Opções de cabeçalho e aba são comuns às fontes da mesma execução; use chamadas separadas para formatos heterogêneos. `--locale pt-BR|en-US` é uma decisão explícita sobre datas e números; sem ela, `1,234` e `01/02/2026` permanecem ambíguos. Números Excel já tipados são preservados como recebidos; zeros exibidos apenas por máscara de formatação não fazem parte do valor armazenado.

Saídas existentes são recusadas. `--overwrite` permite substituir os quatro artefatos gerados; links para fontes originais continuam proibidos. Códigos de saída: `0` diagnóstico gerado, `1` erro de entrada/escrita, `2` BLOCKER com `--fail-on-blocker` (ou erro de argumentos do argparse). Sem a opção estrita, `0` não significa dados validados.

## Artefatos

| Arquivo | Conteúdo |
|---|---|
| `analysis.json` | Resultado completo, versão 0.2.0, origem, perfis, hipóteses, financeiro, relações e ocorrências |
| `profile.json` | Perfis por tabela |
| `plan.json` | Operações propostas, riscos, pré-condições e dependências dos indicadores |
| `report.md` | Leitura humana com limites explícitos de tamanho |

Os JSONs não incluem amostras de células. Incluem nomes de arquivos/abas/colunas, estatísticas agregadas e números de linhas para investigar problemas; trate esses artefatos como dados internos. Conteúdo e ordenação são reproduzíveis com os mesmos arquivos, opções e versões das dependências. Não há timestamps ou caminhos absolutos no resultado.

Exemplo de ocorrência: `paid_without_payment_date`, severidade `BLOCKER`, escopo `cash_metrics`, linhas da origem. Isso impede uma métrica de caixa confiável; contagem de linhas continua disponível. `mixed_currencies` bloqueia agregação entre moedas. `suspected_duplicates` é WARNING e nunca remove registros. `cash_received: requires_contract` indica campos disponíveis, ainda sem cálculo nem confirmação de receita.

## Benchmarks e reconciliação

As bases em [tests/fixtures](tests/fixtures) são inteiramente sintéticas. Para recriá-las:

```powershell
python scripts/generate_benchmarks.py --output tests/fixtures
python -m unittest discover -s tests -v
```

Cobrem financeiro limpo, inconsistente, ambíguo, abas relacionadas, formatos brasileiros/americanos, duplicatas legítimas, transferências/estornos e projetos sem datas. O XLSX também tem bytes reproduzíveis. A API `validation.reconcile(before, after, ['Valor'], 'Moeda')` verifica linhas, células e totais exatos separados por moeda; nenhuma transformação é executada pela CLI.

## Compatibilidade e limites

O comando `analyze`, entrada posicional, `--output`, `--sheet` e `--sep` continuam disponíveis. Os esquemas de saída evoluíram para múltiplas tabelas; consumidores V0.1 devem migrar para `tables`. A CLI não gera mais `layout.json`. Profiler/Gantt/grid/receitas V0.1 permanecem para regressão e experimentação e não validam semântica V0.2.

Esta versão não gera DAX, PBIP, Power Query, modelo dimensional, dashboard, interface gráfica ou screenshots. Não lê SQL, XLS, PDF nem PBIX. Não executa planos, avalia fórmulas, calcula inadimplência ou confirma relações/granularidade. O motor usa memória integral; não é indicado para fontes maiores que a memória disponível. Confiança semântica é força heurística conservadora, sem calibração probabilística empírica. Consulte [contratos e limites](docs/DATA_CONTRACTS.md).

## Documentação

- [Visão do produto](docs/PRODUCT_VISION.md)
- [Auditoria e decisões](docs/AUDIT_V0.2.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Contratos de dados](docs/DATA_CONTRACTS.md)
- [Instruções para agentes](AGENTS.md) e [skill portátil](SKILL.md)

Integrações futuras deverão verificar a documentação vigente de [Microsoft Skills for Fabric](https://github.com/microsoft/skills-for-fabric), [Power BI Modeling MCP](https://github.com/microsoft/powerbi-modeling-mcp) e [PBIR](https://learn.microsoft.com/en-us/power-bi/developer/embedded/projects-enhanced-report-format). Não há integração Microsoft implementada nesta versão.
