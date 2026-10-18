---
name: powerbi-autopilot
description: Diagnostica fontes locais CSV, XLSX e XLSM antes da criação de relatórios Power BI, produzindo perfis, hipóteses semânticas, riscos financeiros e planos auditáveis de transformação. Use para inspecionar dados e avaliar quais indicadores têm evidência suficiente; esta versão não cria dashboards ou projetos Power BI.
---

# PowerBI Autopilot V0.2

## Missão
Compreenda e diagnostique fontes antes de recomendar indicadores. Trabalhe localmente, sem APIs, serviços pagos ou Power BI Desktop. Preserve os arquivos originais.

## Ordem de trabalho
1. Identifique objetivo, fontes e regras regionais conhecidas. Não presuma locale de dados financeiros a partir do idioma da conversa.
2. Execute `python -m powerbi_autopilot.cli analyze <arquivo> [outros arquivos] --output outputs/analysis`. Excel lê todas as abas; use `--sheet` para restringir. Consulte [README.md](README.md) para opções e instalação. Se houver ambiguidade, registre-a; só informe `--locale pt-BR` ou `en-US` quando houver evidência externa suficiente.
3. Leia `analysis.json` e `report.md`. Examine BLOCKER por escopo, conversões, granularidade desconhecida e relações candidatas. Contagens são fatos; papéis semânticos e domínio são hipóteses. Nenhuma confiança heurística confirma significado de negócio.
4. Revise `plan.json`: origem, destino, operação, riscos e pré-condições. Planos não foram executados. Consulte [docs/DATA_CONTRACTS.md](docs/DATA_CONTRACTS.md) para contratos de medidas, severidades e reconciliação.
5. Entregue diagnóstico, interpretações justificadas, dependências de indicadores, ambiguidades e próximos passos. Não calcule receitas/despesas/caixa sem contrato explícito. Não descreva a fonte como validada apenas por ausência de ocorrências.

## Regras invariantes
- Nunca invente datas, valores, metas, moedas, unidades, relacionamentos ou números de projetos.
- Quando a fonte trouxer apenas datas realizadas, não as apresente como datas planejadas.
- Só calcule atraso se existir uma data-alvo/planejada e uma data real ou uma regra de avaliação definida.
- Gantt requer início e fim/duração confiáveis, além de visual compatível. Caso contrário, preferir milestones ou pedir confirmação.
- Não deduza receita de todos os lançamentos positivos sem compreender classificação e granularidade.
- Evite somar campos que representam saldo, estoque ou métricas de snapshot ao longo de datas.
- Não execute fórmulas/macros nem publique ou envie dados privados a APIs.
- Não trate JSON válido como prova de dashboard funcional. A V0.2 não produz DAX, PBIP/PBIR, dashboards ou screenshots.

## Documentos de apoio
- [docs/ROADMAP.md](docs/ROADMAP.md): fronteiras de escopo e integrações futuras.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): responsabilidades e extensibilidade.
- `recipes/`: conhecimentos descritivos V0.1; não são contratos financeiros nem prova de capacidade implementada.

## Execução local
```bash
python -m pip install -r requirements.txt
python -m powerbi_autopilot.cli analyze tests/fixtures/finance_clean.csv --output outputs/clean
python -m unittest discover -s tests -v
```
