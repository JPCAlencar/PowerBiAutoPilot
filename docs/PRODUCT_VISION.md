# PowerBI Autopilot — Visão do Produto e Desenvolvimento V0.2

## 1. Contexto e missão

Estamos desenvolvendo o **PowerBI Autopilot**, uma skill open source, portátil e independente de fornecedor de IA, projetada para permitir que agentes como OpenAI Codex, Claude Code, Gemini CLI e outros agentes compatíveis criem relatórios profissionais de Power BI de ponta a ponta.

O produto deve funcionar como um especialista em engenharia de dados, análise de negócios, modelagem dimensional, DAX e design de dashboards.

**Objetivo final:** receber uma ou várias fontes de dados e uma solicitação em linguagem natural, compreender o contexto de negócio, preparar e validar os dados, construir o modelo analítico, criar medidas, selecionar os indicadores apropriados, gerar um projeto Power BI e verificar visualmente o resultado, corrigindo os problemas encontrados.

Queremos reduzir ao máximo a necessidade de ajustes manuais.

Não queremos apenas um gerador de gráficos. Queremos um sistema capaz de compreender os dados e tomar decisões analíticas justificadas.

A prioridade absoluta é a confiabilidade dos dados. Um dashboard visualmente excelente, mas com cálculos errados, representa uma falha crítica.

## 2. Estado atual do projeto

Existe um starter V0.1 no workspace, contendo:

- Uma skill inicial (`SKILL.md`).
- Scripts Python para leitura e perfil básico de dados.
- Receitas YAML para financeiro, projetos, faturamento e logística.
- Um mecanismo inicial de posicionamento de componentes.
- Verificações básicas relacionadas a Gantt.
- Sete testes automatizados.

Esse código é apenas um protótipo e **não deve limitar a arquitetura futura**.

Antes de implementar, inspecione o repositório, execute os testes existentes e faça uma avaliação técnica objetiva.

Preserve componentes úteis. Refatore ou substitua componentes que não atendam aos requisitos de robustez, extensibilidade e qualidade.

Corrija o manifesto da skill para seguir o formato Agent Skills, incluindo os campos obrigatórios `name` e `description`.

Não considere funcionalidades existentes como prontas apenas porque possuem testes. Avalie a cobertura e a profundidade dos testes.

## 3. Visão funcional completa

O PowerBI Autopilot deverá futuramente executar este fluxo:

1. **Data Intake:** receber Excel, CSV, SQL, arquivos Power BI e outras fontes suportadas.
2. **Data Profiling:** investigar estrutura, tipos, valores, distribuição, integridade e relações entre tabelas.
3. **Semantic Understanding:** compreender o significado provável dos campos e a natureza dos processos representados.
4. **Business Intelligence:** reconhecer o domínio dos dados e sugerir análises relevantes com base em evidências.
5. **Data Engineering:** planejar e executar limpeza, padronização, transformação e modelagem com rastreabilidade.
6. **Semantic Modeling:** construir tabelas fato, dimensões, calendário, relacionamentos e medidas DAX.
7. **Report Planning:** selecionar KPIs, visuais, filtros, páginas e objetivos analíticos.
8. **Visual Design:** aplicar templates profissionais e sistemas de grid para criar layouts consistentes.
9. **Power BI Authoring:** gerar projetos PBIP utilizando PBIR, TMDL, Power Query M e ferramentas oficiais.
10. **Visual Quality Assurance:** abrir ou pré-visualizar relatórios, capturar screenshots, avaliar a qualidade e corrigir problemas.
11. **Delivery:** entregar um projeto funcional, documentação, resultados de testes, limitações e evidências de validação.

Esse é o destino do produto, **não o escopo de implementação desta etapa**.

## 4. Arquitetura estratégica

Adote uma arquitetura modular, com separação clara entre:

- Motor de leitura e inspeção de fontes.
- Motor de análise da qualidade dos dados.
- Motor de interpretação semântica.
- Catálogo de conhecimento e receitas de negócio.
- Planejador de transformações.
- Executor determinístico de transformações.
- Modelador analítico.
- Planejador de relatórios.
- Adaptadores de autoria Power BI.
- Motor de validação técnica e visual.

Não desenvolva um grande sistema monolítico de regras acopladas.

O núcleo de dados deve ser utilizável sem Power BI Desktop e sem qualquer API de IA.

A IA deverá ser responsável por raciocínio, interpretação, planejamento e resolução de ambiguidades. Transformações, cálculos e validações deverão utilizar implementações determinísticas sempre que possível.

O projeto deve funcionar localmente, preferencialmente em Windows, sem exigir Microsoft Fabric, Power BI Service ou serviços pagos.

Utilize Python e dependências maduras. Prefira soluções simples e testáveis a frameworks excessivamente complexos.

As integrações futuras com Microsoft deverão aproveitar:

- https://github.com/microsoft/skills-for-fabric
- https://github.com/microsoft/powerbi-modeling-mcp
- https://learn.microsoft.com/en-us/power-bi/developer/embedded/projects-enhanced-report-format

Consulte a documentação atual antes de implementar integrações. Não suponha que nomes de ferramentas, comandos e interfaces de versões antigas continuam válidos.

## 5. Decisões fundamentais de engenharia de dados

A engenharia de dados será o núcleo do produto.

Adote conceitualmente três estágios:

**Raw:** dados originais preservados, sem alterações destrutivas.

**Clean:** dados padronizados, validados e transformados, com registro de origem e regras aplicadas.

**Analytical:** dados modelados para análises, indicadores, relacionamentos e consumo pelo Power BI.

Esses estágios não exigem um data lake. Podem ser implementados localmente.

Defina claramente a granularidade de cada tabela. Identifique se cada linha representa um lançamento, transação, evento, projeto, atividade, cliente, saldo histórico ou outra entidade.

Não realize joins sem analisar cardinalidade e risco de multiplicação de registros.

Não remova duplicatas automaticamente. Registros aparentemente iguais podem representar transações legítimas.

Não invente datas, valores, classificações, identificadores, saldos ou metas.

Toda transformação relevante deverá ser reproduzível, auditável e testável.

Separe explicitamente fatos observados, inferências fundamentadas, hipóteses e informações desconhecidas.

## 6. Primeiro domínio: Financeiro

Nosso primeiro benchmark será um conjunto de bases financeiras sintéticas que simulem problemas reais de empresas.

A arquitetura deve continuar genérica, mas as primeiras regras especializadas serão financeiras.

O sistema deverá reconhecer possíveis campos relacionados a:

- Entradas, saídas e valores monetários.
- Crédito e débito.
- Datas de lançamento, competência, vencimento e pagamento.
- Pagamentos realizados, pendentes e cancelados.
- Clientes, fornecedores, projetos e centros de custo.
- Categorias, classificações e subgrupos.
- Orçamento, realizado e previsões, quando existirem informações suficientes.

**Não assuma que nomes de colunas são suficientes para definir seu significado.**

Por exemplo, uma coluna chamada `Valor` pode representar uma despesa, receita, saldo, orçamento ou valor acumulado.

Uma coluna chamada `Data` pode representar lançamento, pagamento, competência ou atualização.

Uma coluna chamada `Pago` pode conter booleanos, textos, símbolos ou valores inconsistentes.

A interpretação deve considerar nomes, tipos, distribuições, valores possíveis, relações com outros campos e regras conhecidas de negócio.

Identifique ambiguidades e registre hipóteses com evidências e nível de confiança.

## 7. Regras críticas do domínio financeiro

Implemente mecanismos capazes de detectar problemas como:

- Formatos monetários brasileiros e internacionais.
- Parênteses representando valores negativos.
- Sinais inconsistentes entre `Tipo` e `Valor`.
- Valores numéricos armazenados como texto.
- Datas inválidas ou ambíguas.
- Datas de pagamento ausentes.
- Lançamentos duplicados ou aparentemente duplicados.
- Classificações inconsistentes.
- Valores nulos e registros incompletos.
- Diferentes moedas.
- Possíveis transferências internas.
- Estornos, cancelamentos e reembolsos.
- Relações entre tabelas que podem duplicar valores.

Não corrija automaticamente situações ambíguas.

Diferencie conceitos como receitas previstas, receitas recebidas, despesas incorridas, despesas pagas e saldo de caixa.

Não some saldos de períodos diferentes como se fossem fluxos financeiros.

Não determine inadimplência sem regras e dados suficientes.

Não utilize o sinal do valor como única evidência de receita ou despesa.

Antes de construir indicadores, deverá existir um contrato explícito sobre o significado das medidas.

## 8. Sistema de qualidade e reconciliação

A qualidade deverá ser verificável.

Implemente diagnósticos para:

- Quantidade de registros por fonte e tabela.
- Valores ausentes e percentuais de preenchimento.
- Tipos de dados e falhas de conversão.
- Unicidade e possíveis chaves.
- Duplicidades suspeitas.
- Integridade entre tabelas.
- Distribuições e possíveis anomalias.
- Comparação de totais antes e depois de transformações.
- Rastreabilidade dos registros alterados.
- Invariantes financeiras e regras de domínio.

Crie três níveis de ocorrência:

**BLOCKER:** problema que compromete materialmente um resultado ou impede uma operação segura.

**WARNING:** situação suspeita que requer atenção, mas não necessariamente impede o processamento.

**INFO:** observação ou oportunidade analítica.

Uma transformação que exclua registros ou modifique totais inesperadamente deverá falhar na validação.

A validação deve ser proporcional: um problema em uma métrica específica não precisa bloquear análises independentes que continuam corretas.

Nunca apresente um processo como validado se somente executou testes superficiais.

## 9. Evolução futura para outros domínios

A arquitetura deve permitir adicionar receitas específicas sem modificar o núcleo do motor.

Domínios previstos:

**Acompanhamento de projetos:** cronogramas, Gantt, marcos, progresso, atrasos e responsáveis.

**Faturamento:** metas, realizado, crescimento, tendências e concentração.

**Logística:** lead time, produtividade, SLA, atrasos e volumes.

**Dashboards executivos:** indicadores prioritários, evolução, riscos e comparações.

Exemplo importante: para criar um Gantt, o sistema deve procurar datas de início e fim ou duração válidas. Se só encontrar datas de atualização ou conclusão, deve reconhecer essa limitação. Pode propor um início observado ou estimado, claramente identificado, mas nunca apresentá-lo como fato comprovado.

Esse princípio de não inventar dados deverá ser aplicado a todos os domínios.

Não implemente essas especialidades completas nesta etapa. Apenas garanta que a arquitetura permita adicioná-las.

## 10. Escopo exato desta implementação: V0.2

Implemente agora um **Data Intelligence Engine**, concentrado na compreensão e no diagnóstico dos dados.

Entregas funcionais esperadas:

**A. Ingestão robusta**

Ler CSV, XLSX e XLSM, incluindo múltiplas abas e opções de formato.

Detectar ou diagnosticar codificação, delimitadores, tipos, cabeçalhos problemáticos e formatos regionais quando possível.

Preservar a origem dos dados e produzir erros compreensíveis para formatos não suportados.

Não executar macros de planilhas.

**B. Data Profiling**

Analisar colunas, tipos, preenchimento, cardinalidade, distribuição, possíveis chaves, granularidade e qualidade dos registros.

Identificar possíveis relacionamentos entre tabelas sem presumir sua validade.

Evitar relatórios excessivamente grandes ou exposição desnecessária de dados sensíveis.

**C. Semantic Mapping**

Construir um mecanismo extensível de identificação semântica de colunas.

Usar regras, metadados e evidências estatísticas.

Produzir sugestões com justificativas e confiança calibrada.

Diferenciar detecção heurística de validação definitiva.

**D. Financial Analysis**

Criar um diagnóstico financeiro especializado que reconheça campos monetários, temporais, classificações e tipos de movimento.

Sugerir indicadores possíveis e indicar quais dependem de informações adicionais.

Não construir medidas DAX nesta versão.

**E. Transformation Planning**

Criar uma representação estruturada das transformações necessárias, incluindo origem, destino, tipo de operação, justificativa, riscos e pré-condições.

Nesta V0.2, priorize diagnóstico e planejamento. Não execute correções destrutivas ou ambíguas.

**F. Validation Engine**

Criar regras automatizadas de qualidade e reconciliação para os casos já suportados.

Produzir resultados verificáveis com severidade e evidências.

**G. CLI e artefatos**

Manter compatibilidade razoável com o comando `analyze` existente, ampliando suas funcionalidades.

Gerar resultados estruturados em JSON e relatórios legíveis em Markdown.

Documentar esquemas, campos e limitações.

**H. Testes**

Criar dados sintéticos realistas para os seguintes cenários:

- Financeiro limpo.
- Financeiro com dados inconsistentes.
- Financeiro com informações semanticamente ambíguas.
- Arquivo Excel com múltiplas abas relacionadas.
- Formatos regionais de números e datas.
- Registros duplicados legítimos.
- Transferências ou estornos que não podem ser interpretados como receitas comuns.
- Datas ausentes em uma base de projetos.

Implementar testes unitários e de integração, inclusive regressão para os testes existentes.

Testar também casos em que o sistema deve recusar uma inferência ou declarar que não dispõe de evidência suficiente.

## 11. Critérios de aceite da V0.2

A versão só estará concluída quando:

1. Conseguir inspecionar corretamente as bases sintéticas fornecidas.
2. Identificar problemas relevantes e classificar sua severidade.
3. Produzir interpretações financeiras justificadas.
4. Evitar conclusões indevidas nos cenários ambíguos.
5. Preservar integralmente os arquivos originais.
6. Gerar artefatos reproduzíveis e legíveis.
7. Passar nos testes automatizados.
8. Manter a arquitetura preparada para novas receitas.
9. Documentar claramente as funcionalidades não implementadas.
10. Não depender de Power BI Desktop, APIs externas ou serviços pagos nesta etapa.

Não quero testes criados apenas para confirmar implementações superficiais. Quero casos capazes de encontrar erros reais de engenharia de dados.

## 12. Organização e documentação

Organize o projeto de maneira profissional, mas sem burocracia ou abstrações desnecessárias.

Crie ou atualize:

- `README.md`: instalação, execução e exemplos.
- `AGENTS.md`: instruções permanentes para agentes que desenvolverão o projeto.
- `SKILL.md`: instruções da skill, com metadados corretos.
- `docs/PRODUCT_VISION.md`: visão completa descrita neste briefing.
- `docs/ARCHITECTURE.md`: responsabilidades, dependências e decisões.
- `docs/ROADMAP.md`: etapas e critérios de aceite.
- `docs/DATA_CONTRACTS.md`: contratos de entrada, saída, semântica e qualidade.

Utilize outros diretórios conforme a necessidade técnica.

Mantenha o SKILL.md conciso e utilize referências complementares para os conhecimentos especializados. Não coloque toda a documentação do produto dentro do contexto da skill.

## 13. Segurança, privacidade e portabilidade

O projeto deverá funcionar inicialmente de maneira local e offline.

Não envie dados financeiros ou pessoais para APIs externas.

Não armazene credenciais em arquivos versionados.

Não execute código contido nas planilhas.

Não sobrescreva arquivos originais.

Evite registrar dados sensíveis em logs.

Separe qualquer integração futura com LLMs por interfaces substituíveis.

A skill deve ser compatível com o padrão aberto de Agent Skills, evitando dependência exclusiva do Codex.

## 14. Forma de execução

Trabalhe em duas fases dentro desta tarefa.

**Fase A — Auditoria e planejamento**

Inspecione o código, execute os testes, identifique limitações e estabeleça a arquitetura necessária.

Registre as principais decisões técnicas, incluindo quais partes serão reaproveitadas, refatoradas ou substituídas.

Não considere o starter como arquitetura obrigatória.

**Fase B — Implementação**

Após a auditoria, prossiga com a implementação completa da V0.2, sem aguardar aprovação intermediária para decisões técnicas comuns.

Implemente os módulos, crie as bases sintéticas, execute os testes, corrija as falhas e atualize a documentação.

Evite dedicar a maior parte do esforço à elaboração de planos sem produzir código funcional.

Ao concluir, entregue um relatório com:

- Arquitetura implementada.
- Funcionalidades reais.
- Testes executados e resultados.
- Exemplos de diagnósticos gerados.
- Limitações conhecidas.
- Dívida técnica relevante.
- Próximo passo recomendado para V0.3.

**Importante:** não implemente ainda a interface gráfica, o dashboard financeiro, o PBIP, o DAX ou o sistema de screenshots.

O objetivo desta etapa é criar uma base sólida de compreensão e validação de dados.

Nosso compromisso é com confiabilidade, extensibilidade, rastreabilidade e qualidade. Prefira uma V0.2 menor e bem testada a uma implementação grande, superficial e difícil de manter.

Comece auditando o repositório e depois implemente a V0.2.