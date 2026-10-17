---
name: powerbi-autopilot
summary: Analisa fontes tabulares, interpreta objetivos de negócio, planeja modelagem e visuais e coordena a criação/validação de relatórios Power BI usando ferramentas oficiais.
---

# PowerBI Autopilot (protótipo 0.1)

## Missão
Crie relatórios Power BI úteis e bem acabados, começando pela compreensão da fonte. Nunca assuma que os dados suportam uma métrica sem inspecionar as colunas e os registros.

## Ordem de trabalho
1. **Intake e privacidade.** Identifique objetivos, público, origem, política de confidencialidade, idioma, fuso horário e atualização. Trabalhe localmente com fontes sensíveis; não publique nem envie dados sem autorização.
2. **Perfil e semântica.** Execute `python -m powerbi_autopilot.cli analyze <arquivo> --output ./analysis`. Examine `profile.json`, `plan.json` e `layout.json`; confira tipos, preenchimento, datas, unidades e granularidade. A detecção automática de domínio é apenas uma sugestão.
3. **Receitas.** Consulte `recipes/*.yaml` para condições, pré-requisitos e oportunidades de análise. Especialmente em cronogramas: não crie datas fictícias. Se faltar início/fim, documente bloqueio ou suposição aprovada.
4. **Plano validado.** Descreva perguntas de negócio, fatos e dimensões, relacionamento de tabelas, regras de cálculo, medidas DAX desejadas, visuais, dependências e limitações. O arquivo `plan.json` é um rascunho interno, **não** o contrato oficial PBIR.
5. **Implementação.** Se disponíveis, use as skills oficiais Microsoft `semantic-model-authoring` e `powerbi-report-cli` do repositório `microsoft/skills-for-fabric`, e Power BI Modeling MCP, em vez de inventar estrutura PBIR ou propriedades de visuais. Converta o plano ao `Design Brief` oficial segundo a documentação da versão instalada.
6. **Validação.** Valide DAX/relacionamentos com o modelo real, execute a validação PBIR, abra/recarregue o relatório e revise screenshots de TODAS as páginas afetadas. Itere até resolver problemas. Se não houver Desktop ou ambiente de preview, registre **bloqueado**, nunca declare a renderização validada.
7. **Entrega.** Entregue PBIP/PBIR, fontes transformadas, regras aplicadas, testes, resultados e limitações. Publicação/compartilhamento e substituição de arquivos originais exigem autorização.

## Regras invariantes
- Nunca invente datas, valores, metas, moedas, unidades, relacionamentos ou números de projetos.
- Quando a fonte trouxer apenas datas realizadas, não as apresente como datas planejadas.
- Só calcule atraso se existir uma data-alvo/planejada e uma data real ou uma regra de avaliação definida.
- Gantt requer início e fim/duração confiáveis, além de visual compatível. Caso contrário, preferir milestones ou pedir confirmação.
- Não deduza receita de todos os lançamentos positivos sem compreender classificação e granularidade.
- Evite somar campos que representam saldo, estoque ou métricas de snapshot ao longo de datas.
- Não trate JSON válido como prova de dashboard funcional.
- Respeite o esquema e os comandos reais da versão instalada das ferramentas Microsoft.

## Documentos de apoio
- `docs/roadmap.md`: marcos e critérios de aceite.
- `docs/architecture.md`: motor do protótipo, integração e escopo.
- `recipes/`: padrões e pré-requisitos por domínio.

## Execução local
```bash
python -m pip install -r requirements.txt
python -m powerbi_autopilot.cli analyze examples/projetos.csv --output analysis
python -m unittest discover -s tests -v
```
