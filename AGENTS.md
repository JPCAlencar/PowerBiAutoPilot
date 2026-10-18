# Desenvolvimento do PowerBI Autopilot

Leia README.md, docs/ARCHITECTURE.md e docs/DATA_CONTRACTS.md antes de alterar o motor. docs/PRODUCT_VISION.md é a visão; docs/ROADMAP.md delimita cada versão. O estágio atual é V0.2: diagnóstico e planejamento offline, sem autoria Power BI.

- Preserve fontes byte a byte. Não execute macros, fórmulas ou código vindo dos arquivos. Não envie dados a APIs. Não versione credenciais ou bases privadas.
- Não invente valores, datas, moedas, identificadores, metas ou granularidade. Nome de coluna e sinal monetário são evidências insuficientes para definir significado financeiro.
- Mantenha fatos, inferências, hipóteses e desconhecidos identificáveis nos contratos. Confiança heurística não deve ser chamada de probabilidade validada.
- Não faça joins sem analisar cardinalidade, nulos, cobertura e multiplicação. Duplicatas iguais podem ser legítimas; nunca removê-las automaticamente.
- Toda operação futura deverá declarar pré-condições, política de valores/sinais/moedas e reconciliação. Comparar somente totais é insuficiente: preservar identidade e investigar células alteradas.
- Ocorrências devem trazer severidade, escopo, contagem e evidência limitada. Não imprimir valores de células nem caminhos privados em erros.
- Mantenha núcleo importável sem CLI, Desktop, modelos de IA ou serviços. Regras semânticas adicionais entram por SemanticRule; domínios novos usam módulos próprios e contratos comuns. Não estender o legado V0.1 para realizar diagnósticos V0.2.
- Escreva regressões que possam encontrar um erro real antes de corrigir comportamento. Use bases sintéticas. Execute `python -m unittest discover -s tests -v` e as chamadas CLI relevantes. Não confunda testes aprovados com validação de dados reais ou renderização.
- Versione alterações incompatíveis de JSON e documente migração. Preserve saídas determinísticas, decimais em strings e ausência explícita de dados.
- Integrações Microsoft futuras exigem consulta às interfaces e esquemas oficiais atuais. Não fabricar PBIR/DAX ou alegar validação visual sem executar o ambiente correspondente.

Comandos úteis: `python scripts/generate_benchmarks.py`, `python -m powerbi_autopilot.cli analyze tests/fixtures/finance_clean.csv --output outputs/check`, `python -m unittest discover -s tests -v`.
