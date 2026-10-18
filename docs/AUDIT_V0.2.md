# Auditoria e plano V0.2 — 2026-10-16

## Evidências do starter

Baseline: commit `d9dc47c`, árvore limpa; `python -m unittest discover -s tests -v`: 7 testes passaram. A cobertura é estreita: cinco casos de datas/Gantt e dois de limites/sobreposição. Não comprova ingestão financeira, integridade, semântica ou reconciliação.

Problemas: CSV fixo em UTF-8/vírgula; Excel lê só a primeira aba; pandas pode ocultar cabeçalhos duplicados e converter identificadores; datas regionais são presumidas; receitas classificam apenas por nomes; ausência de metadados de origem, severidades e contrato de métricas. Manifesto usa `summary` em vez de `description`. Não existe execução nem validação real de Power BI.

## Decisões e desenho

- Reaproveitar grid, receitas descritivas e interfaces públicas do profiler para compatibilidade. Isolar esses recursos legados do diagnóstico V0.2.
- Substituir ingestão da CLI por leitor local com múltiplas fontes/abas, SHA-256, linhas de origem, cabeçalhos posicionais e erros compreensíveis. Nunca executar macros/fórmulas.
- Adotar módulos Python pequenos, pandas/openpyxl já disponíveis, Decimal para valores exatos e parsers conservadores. Sem IA, serviços ou Desktop.
- Perfis completos em contagens, mas sem amostras de valores. Relacionamentos são candidatos com cobertura, cardinalidade e risco de multiplicação, nunca joins automáticos.
- Semântica extensível por regras registráveis, combinando nomes e evidência de valores. Confiança é força heurística, sem probabilidade estatística. Significado final sempre depende de contrato revisado.
- Financeiro apenas diagnostica e sugere métricas condicionais; não calcula receitas a partir de sinais, não soma moedas/saldos nem executa planos.
- Raw permanece nos arquivos originais; Clean/Analytical são estágios planejados. Reconciliação independente compara identidade de linhas, células e totais Decimal por moeda, com diferenças esperadas explicitamente declaradas.
- JSON versionado, determinístico e Markdown escapado. Resultados nunca representam fontes ambíguas como validadas.

Alternativas descartadas: ampliar o monólito de regras por nomes (baixo custo, alto risco semântico); introduzir framework de pipelines/LLM (complexidade sem benefício nesta etapa).

## Plano de execução e verificação

1. Escrever testes que falham para ingestão, parsers e preservação; implementar contratos e leitura.
2. Escrever testes para perfis, relações, semântica e recusa; implementar módulos independentes.
3. Testar inconsistências financeiras, planos e reconciliação, inclusive perda de linhas e compensação de valores; implementar sem executar correções.
4. Integrar CLI compatível com `analyze`, formatos JSON/Markdown e opções regionais; testar reprodução, privacidade, erros e proteção das entradas.
5. Gerar benchmarks sintéticos determinísticos, documentação e manifesto; executar suíte completa, CLI em todos os cenários e revisão independente.

Revisar especialmente: ambiguidade de datas/números, nulos em chaves, fórmulas sem cache, sinal versus natureza, relações muitos-para-muitos e proteção contra sobrescrita.

## Registro

- Fase A concluída: baseline e limites inspecionados.
- Execução no workspace solicitado, sem alterações de branch/commits automáticos. O briefing dispensa aprovações técnicas intermediárias; não haverá gates adicionais de desenho.
- Integrações Microsoft ficam fora da V0.2; sua documentação atual deverá ser consultada quando forem implementadas.
- Fase B concluída: módulos, benchmarks, CLI, testes e documentação implementados; resultados e limites em DELIVERY_V0.2.md.
- Refinamento após revisão: aritmética Decimal dimensionada aos operandos, regras monetárias compartilhadas e com limites de token, diagnóstico de fórmulas no cabeçalho, verificação de identidade/proveniência e recusa de moedas contraditórias.
- Reconciliação V0.2 é estrita; deltas esperados e trilhas de execução de transformações ficam para V0.3, em vez de aceitar alterações ainda sem contrato.
