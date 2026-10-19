# Arquitetura V0.2.1

O núcleo é uma biblioteca Python offline. A CLI é apenas uma porta de entrada. Nenhum módulo depende de Power BI Desktop, APIs de IA ou serviços Microsoft.

```text
CSV / XLSX / XLSM
        ↓ intake → Table (origem, SHA-256, DataFrame, linhas da origem)
        ↓ profiling + parsing → fatos observados e falhas de conversão
        ↓ semantics → hipóteses com evidências e força heurística
        ↓ financial → regras financeiras e dependências de indicadores
        ↓ planning → transformações propostas, sem execução
        ↓ relationships + validation → riscos e severidades por escopo
        ↓ reporting → analysis.json, profile.json, plan.json, report.md
```

## Responsabilidades e dependências

| Módulo | Responsabilidade | Dependências relevantes |
|---|---|---|
| `contracts` | Table, ocorrência com severidade/escopo/linhas | pandas |
| `intake` | Leitura conservadora, cabeçalhos, todas as abas, hash | csv, openpyxl, contracts |
| `parsing`, `exact` | Conversão escalar e aritmética decimal exata | biblioteca padrão, pandas para nulos |
| `profiling` | Contagens, unicidade, distribuições, datas, duplicatas | parsing, contracts |
| `semantics` | Regras registráveis e evidência de nomes/valores | contratos de perfil |
| `financial` | Diagnósticos de moeda/status/natureza e contratos de medidas | perfis, semântica, parsing |
| `relationships` | Cardinalidade, cobertura, órfãos e risco de multiplicação | Table, contadores |
| `planning` | Origem/destino, riscos e pré-condições por operação | perfis e mapeamento |
| `validation` | Sumário por escopo e reconciliação independente | Table, parsing, exact |
| `engine` | Orquestração e verificação final dos hashes | módulos acima |
| `reporting`, `cli` | Serialização, Markdown limitado e escrita protegida | engine e biblioteca padrão |

`profiler`, `recipes`, `gantt` e `layout` preservam interfaces V0.1 para regressão. A normalização textual do profiler é reutilizada; sua inferência regional legada não é chamada pelo novo motor. Catálogos YAML antigos são conhecimento descritivo, não regras executáveis V0.2.

## Decisões

Raw é o arquivo original preservado; não é duplicado para um lake. SHA-256 identifica o conteúdo e as linhas guardam a origem. Clean e Analytical são destinos declarados, sem materialização nesta versão. Leitura não executa fórmulas ou macros e não usa cache de fórmulas como verdade. Cabeçalhos problemáticos recebem nomes posicionais e diagnósticos; seu mapeamento original permanece disponível.

Semântica utiliza nomes e proporção de valores compatíveis. Confiança é força heurística ordinal e conservadora, reduzida para amostras pequenas, ambiguidade e campos genéricos. Não há dados suficientes para probabilidade calibrada; todos os papéis permanecem hipóteses. Granularidade permanece desconhecida, mesmo com chaves únicas.

Indicadores financeiros são sugestões com requisitos, nunca valores calculados. Um BLOCKER é associado à coluna ou operação afetada. O diagnóstico geral pode conter bloqueios enquanto contagem de linhas e análises independentes continuam utilizáveis.

Reconciliação usa Decimal com precisão dimensionada aos operandos e soma separada por moeda explícita. Compara também identidade de linhas, esquema e células: alterações compensatórias não passam por terem total igual. A API atual é estrita: até conversões legítimas de representação requerem um executor e contrato de mudanças futuras. Não aceita deltas esperados nesta versão.

Nenhum join é materializado. Candidatos são restritos a nomes de identificadores iguais normalizados; cardinalidade e cobertura não provam relação de negócio. Nulos são contados separadamente e sua política permanece indefinida. A busca detalha no máximo 100 candidatos e declara truncamento.

V0.2.1 concentra correções nos módulos existentes. `parsing` usa a mesma gramática
de agrupamento em todos os caminhos, recusando grupos iniciais com zero.
`semantics` compartilha comparação controlada de aliases e vocabulário de
pagamento contextual com `financial`; auditoria de campos inválidos não promove
papéis semânticos. `intake` valida separadores contra o cabeçalho lógico e mantém
hipótese explícita de coluna única. Um adaptador pequeno de `ExcelReader` ignora
chartsheets antes do carregamento de desenhos (inclusive a falha de chartsheet
vazia do openpyxl 3.1.5); não altera bytes nem aplica monkey patch global. Essa
interface da dependência requer regressões ao atualizar openpyxl.

`profiling` detecta possíveis linhas agregadas como inferência de layout sem
filtrar o DataFrame. `financial` acrescenta requisito de política de grão e
`planning` propõe revisão. `relationships` calcula multiplicação somente em
correspondências não nulas, mantendo direcionalidade real e política de nulos
indefinida. Engine e esquema JSON 0.2.1 distinguem o novo delimitador anulável;
consulte a migração em DATA_CONTRACTS.md.

JSON não inclui amostras de valores; Markdown escapa metadados e limita listagens. Dados agregados também podem ser sensíveis, portanto as saídas permanecem locais. Escrita faz preflight de todos os destinos e substituição atômica por arquivo; o conjunto não é uma transação e uma interrupção de disco pode produzir saída parcial. Sem `--overwrite`, destinos existentes são recusados.

## Extensão

Uma nova interpretação simples pode fornecer `SemanticRule(role, aliases, kind)` a `map_columns(..., rules=[...])`. Tipos de evidência disponíveis: number, date, movement, status, currency, category, identifier e text. Regras complexas de novos domínios devem ficar em módulos separados que consumam Table/perfil/mapeamento e produzam ocorrências e sugestões; não devem modificar o parser ou acoplar o núcleo ao domínio. Não há descoberta automática de plugins.

Receitas futuras deverão carregar metadados e regras por uma interface explícita, não executar código do usuário embutido em planilhas. Executor determinístico, modelador analítico, planejador de relatórios, adaptadores Microsoft e QA visual são camadas futuras, ainda sem implementações fictícias. Uma integração LLM futura deverá ser opcional, substituível e separada do cálculo.

## Dívida técnica

Processamento integral em memória; busca de relações por nomes ainda limitada; chave composta e grão não inferidos; vocabulário financeiro parcial; calibração semântica precisa de benchmark anotado maior; contratos JSON descritos e versionados sem validador JSON Schema em runtime; sem API para aprovar e executar planos; sem contrato para mudanças esperadas na reconciliação. Ver [roadmap](ROADMAP.md).
