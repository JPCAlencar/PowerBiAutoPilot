# Roadmap e critérios de aceite

## V0.2 — compreensão e diagnóstico (etapa atual)

- Ingestão CSV/XLSX/XLSM com todas as abas, formatos configuráveis, origem e hashes.
- Perfil de contagens, nulos, conversões, unicidade, distribuição, duplicatas e grão desconhecido.
- Hipóteses semânticas extensíveis e diagnóstico financeiro conservador.
- Relações candidatas com cardinalidade, órfãos, nulos e multiplicação.
- Planos declarativos sem execução; validação por escopo e API de reconciliação.
- CLI, JSON determinístico, Markdown legível e documentação portátil.

Aceite: os oito cenários sintéticos precisam ser inspecionados; inferências indevidas recusadas; perdas de registros e alterações não aprovadas detectadas; fontes preservadas; saídas reproduzíveis; suíte e regressões V0.1 aprovadas; nenhuma dependência de Desktop, IA ou serviços. Exemplos e resultados estão em DELIVERY_V0.2.md. Isso não constitui comprovação de interpretação correta para qualquer base real.

V0.2.1 estabiliza o QA independente: conversões sem magnificação por agrupamento
com zero, semântica contextual, CSV de coluna única, chartsheets, multiplicação
não nula e suspeitas de totais preservados. Evidências e limitações em
QA_RESOLUTION_V0.2.1.md. Não antecipa o executor da V0.3.

## V0.3 — contratos revisáveis e execução determinística

Próximo passo recomendado: formalizar e validar contratos de grão/medidas/locale/moedas, permitir aprovação explícita de um plano e executar somente conversões inequívocas para Clean. Registrar por célula origem, regra aplicada e valor antes/depois em trilha local com acesso controlado; não nos logs comuns. Reconciliação deve aceitar apenas diferenças contratadas e rejeitar perdas ou alterações imprevistas. Adicionar chaves compostas e relações com nomes distintos mediante mapeamento explícito.

Aceite: execução idempotente e reproduzível; Raw byte a byte preservado; conversões exatas e totais por moeda reconciliados; falha atômica diante de qualquer pré-condição não atendida; nenhuma exclusão automática de duplicatas; casos anotados para avaliar precisão/recusa semântica. Testar invariantes e casos negativos, não apenas sucesso.

## Modelagem analítica e autoria Power BI (etapas posteriores)

Modelar fatos/dimensões/calendário a partir de grão e contratos confirmados. Depois integrar ferramentas oficiais para TMDL, Power Query M, DAX e PBIP/PBIR, consultando documentação e versão instaladas. Aceite: resultados reconciliados com fontes e medidas verificadas em modelo real.

Planejar e criar relatórios com templates/grid e objetivos analíticos; validar esquema, renderização e screenshots reais em todas as páginas. Ausência de Desktop/preview deve ser declarada, sem alegar QA visual. Só então expandir especialidades de projetos, faturamento, logística e executivos.

As referências estratégicas são skills-for-fabric, powerbi-modeling-mcp e PBIR da Microsoft; nenhuma interface antiga deve ser presumida válida. Publicação e serviços pagos não são dependências do núcleo.
