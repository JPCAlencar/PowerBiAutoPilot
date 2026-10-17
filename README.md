# PowerBI Autopilot — Starter 0.1

Um **primeiro núcleo funcional**, ainda não um gerador PBIP completo. Analisa Excel/CSV, sugere especialidade e visuais, verifica pré-requisitos para Gantt e cria um esboço com coordenadas determinísticas em grid de 12 colunas.

## Rodar (Python 3.10+)
```bash
python -m pip install -r requirements.txt
python -m powerbi_autopilot.cli analyze examples/projetos.csv --output analysis
python -m unittest discover -s tests -v
```

Para Excel com várias abas, indique `--sheet NomeDaAba` (sem isso, a primeira aba é usada no MVP). CSV aceita `--sep ';'`.

Arquivos gerados em `analysis/`:
- `profile.json`: colunas, tipos sugeridos, faltantes, indicadores básicos e alerta de qualidade.
- `plan.json`: sugestão de domínio, análises, dependências e riscos; sujeito à revisão.
- `layout.json`: retângulos em pixels num canvas 1920×1080 a partir de um grid de 12 colunas; não é PBIR.

A lógica que realmente grava `.pbip/.pbir`, TMDL e medidas DAX **não está implementada neste starter**. Essa camada deve usar as ferramentas oficiais da Microsoft conforme `SKILL.md`. A revisão de screenshots também é uma etapa prevista, não implementada pelo script local.

## Referências oficiais
- https://github.com/microsoft/skills-for-fabric
- https://github.com/microsoft/powerbi-modeling-mcp
- https://learn.microsoft.com/en-us/power-bi/developer/embedded/projects-enhanced-report-format

## Segurança
Este protótipo processa os dados localmente; os perfis incluem estatísticas, não exemplos de valores pessoais. Não envie planilhas sigilosas a serviços externos sem autorização.
