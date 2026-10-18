# Entrega V0.2 — 2026-10-16

## Resultado e arquitetura

Data Intelligence Engine implementado como biblioteca Python offline, independente de IA, Desktop e serviços. Ingestão, parsing/aritmética exata, perfis, hipóteses semânticas, diagnóstico financeiro, relacionamentos, planejamento, validação, orquestração e apresentação ficam em módulos separados. [Arquitetura](ARCHITECTURE.md) e [contratos](DATA_CONTRACTS.md) descrevem as interfaces.

O starter foi auditado antes da implementação: 7 testes passaram, com cobertura apenas de Gantt/grid/datas. Foram preservados como regressão, sem tratar a existência desses testes como prova de capacidade financeira. [Auditoria e decisões](AUDIT_V0.2.md).

## Funcionalidades verificadas

- CSV com codificação/delimitador configuráveis, fallback diagnosticado, cabeçalhos vazios/repetidos e erro em linhas irregulares; XLSX/XLSM com todas as abas e seleção por nome.
- Preservação de fontes e IDs textuais; SHA-256, linha de origem e metadados de cabeçalho. Macros/fórmulas nunca executadas; fórmulas inclusive em cabeçalhos geram BLOCKER.
- Contagens, preenchimento, unicidade, chaves candidatas, distribuições, datas, conversões inválidas/ambíguas e duplicatas suspeitas preservadas.
- Hipóteses de campos financeiros com evidência e força heurística. Datas genéricas não viram datas de pagamento. Sinal não define receita. Saldo não vira fluxo.
- Diagnósticos de status desconhecido, pagamento sem data, sinais suspeitos, moedas mistas/conflitantes, categorias variantes, transferências, cancelamentos e estornos.
- Relações candidatas com cardinalidade, órfãos, nulos e risco de multiplicação, sem materializar joins.
- Indicadores sugeridos com dependências e exigência de contrato; somente contagem de linhas é fato diretamente disponível. Nenhum indicador monetário é calculado.
- Planos estruturados sem execução. Severidades BLOCKER/WARNING/INFO e bloqueios proporcionais por escopo.
- API de reconciliação: identidade/quantidade de linhas, esquema, origem, mudanças de células e totais Decimal por moeda. Detecta alterações compensatórias, perdas e divergências; permite reordenação com linhagem.
- CLI compatível com analyze e opções anteriores, múltiplas fontes, JSON determinístico e Markdown legível. Proteção contra sobrescrita de fontes por caminho, link simbólico ou hardlink.
- SKILL.md conciso com name/description, AGENTS.md e visão integral do produto em PRODUCT_VISION.md.

## Testes e revisão

`python -m unittest discover -s tests -v`: **53 testes aprovados**, incluindo os 7 originais. O projeto usa unittest; pytest não está instalado nem é necessário. Não foi medida porcentagem de cobertura.

Os novos testes cobrem os oito cenários solicitados (nove arquivos, pois há formatos BR e US), casos de recusa, preservação byte a byte, privacidade de valores textuais, saída reproduzível, códigos da CLI, proteção de escrita, integrações reais CSV/Excel e reconciliação. O gerador de benchmarks produz CSV e XLSX com bytes reproduzíveis.

Revisão independente de código e probes adversariais encontraram e motivaram regressões para: precisão Decimal além de 28 dígitos e cancelamento/reordenação; moeda embutida sob cabeçalho genérico; moeda contraditória na reconciliação; fórmula no cabeçalho; proveniência incompleta; prefixos de palavras como Europe que não são EUR. Os achados importantes foram corrigidos e reverificados.

Também executados: compileall dos módulos/scripts/testes, git diff --check e quick_validate.py do skill-creator (`Skill is valid!`). Isso valida a estrutura do manifesto, não garante comportamento de todos os agentes de IA.

## Exemplos de diagnóstico

Com opções regionais padrão, a execução CLI dos nove arquivos em tests/fixtures produziu:

| Benchmark | Tabelas | Linhas | BLOCKER | WARNING | Exemplos |
|---|---:|---:|---:|---:|---|
| finance_clean | 1 | 8 | 0 | 1 | Datas ausentes em pagamentos pendentes; sem falsos pagamentos inferidos |
| finance_dirty | 1 | 9 | 5 | 3 | Valor/data inválidos, moedas mistas, status desconhecido e pagamento sem data |
| finance_ambiguous | 1 | 3 | 4 | 1 | Números e datas ambíguos; natureza e moeda desconhecidas |
| finance_related | 3 | 12 | 2 | 2 | Relações com duplicação potencial e órfãos; direções avaliadas separadamente |
| legitimate_duplicates | 1 | 3 | 0 | 1 | Uma repetição suspeita preservada |
| transfers_reversals | 1 | 5 | 0 | 3 | Política própria exigida para transferências/estornos/cancelamentos |
| projects_missing_dates | 1 | 2 | 1 | 1 | Cronograma bloqueado; início não inventado |
| regional_br | 1 | 3 | 2 | 0 | 1.234 e 01/02/2026 permanecem ambíguos |
| regional_us | 1 | 2 | 0 | 0 | Formatos inequívocos presentes no exemplo |

Todos os hashes de entrada permaneceram iguais. Com locale pt-BR explícito, regional_br elimina os dois bloqueios de conversão. Saídas locais completas estão em outputs/benchmarks; [exemplo financeiro](../examples/diagnostics/finance_dirty.md) e [exemplo de múltiplas abas](../examples/diagnostics/finance_related.md) são snapshots legíveis versionados. As contagens são ocorrências de regras, não número de células ou transações incorretas.

## Limitações e dívida técnica

Não há interface, dashboard, PBIP, DAX, Power Query, modelagem dimensional ou screenshots. Nenhuma integração Microsoft foi implementada. SQL/XLS/PBIX não são suportados. Nenhuma correção, deduplicação ou inferência ambígua é executada.

Granularidade e semântica permanecem desconhecidas ou hipotéticas até revisão. Confiança não foi calibrada estatisticamente; nomes e vocabulários têm cobertura limitada. Relações usam nomes de identificadores iguais, sem chaves compostas ou descoberta exaustiva. O catálogo YAML V0.1 não dirige automaticamente as regras V0.2. Uso integral de memória limita a escala; saída não tem transação de múltiplos arquivos. O mecanismo de reconciliação é estrito e não aceita ainda mudanças legítimas aprovadas por contrato. Não há validador JSON Schema em runtime nem política/CLI de aprovação de planos.

## Próximo passo recomendado

V0.3: contratos revisáveis de grão/medidas/moedas/sinais e executor determinístico para conversões inequívocas Raw → Clean, com idempotência, trilha de mudanças e reconciliação que permita somente diferenças contratadas. Expandir o benchmark anotado para avaliar precisão e recusa semântica antes de integrar autoria Power BI.
