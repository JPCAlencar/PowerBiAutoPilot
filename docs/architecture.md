# Arquitetura 0.1

Pipeline inicial: arquivo local → perfil do dataframe → detector heurístico de domínio → receitas de negócio → plano proposto → grade em pixels.

Decisões:
- O plano é marcado `draft_requires_review`: detectar colunas por nomes é probabilístico, não evidência de interpretação de negócio correta.
- O planejamento interno é independente do JSON PBIR e do `Design Brief` oficial. Adaptador oficial fica para a próxima versão.
- A implementação Power BI ocorre por skill Microsoft `powerbi-report-cli` e `semantic-model-authoring`, preferindo Modeling MCP quando disponível.
- Preview e screenshot devem ser validados no ambiente Power BI; não simular screenshots.
- O projeto final deve guardar provenance: regras aplicadas, decisões, suposições e advertências.

Camadas futuras: inteligência de múltiplas tabelas, detecção de chaves e joins; insights estatísticos testáveis; receitas especializadas; gerador/validadores oficiais; inspeção visual automática.
