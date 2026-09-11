Framework genérico para monitoramento de documentos fiscais eletrônicos
recebidos via os web services de Distribuição de DF-e da SEFAZ
(Ambiente Nacional).

Este módulo é **agnóstico ao tipo de documento fiscal**: ele implementa
toda a lógica comum de distribuição DF-e — paginação de NSUs, agendamento
inteligente baseado na resposta da SEFAZ (138, 137, 656), desduplicação,
notificações, logs SOAP e o painel (banner) — parametrizado por tipo de
documento (`fiscal_type`).

Os módulos específicos implementam apenas o que é particular de cada
documento fiscal:

- `l10n_br_nfe_dfe` — DF-e de NF-e (NFeDistribuicaoDFe,
  [NT 2014.002](https://www.nfe.fazenda.gov.br/portal/exibirArquivo.aspx?conteudo=P0U3lU1Fe40=))
- `l10n_br_cte_dfe` — DF-e de CT-e (CTeDistribuicaoDFe) — futuro

Funcionalidades genéricas:

- **Motor de distribuição** em `res.company`, parametrizado por
  `fiscal_type` (campos `{fiscal_type}_last_nsu`, `{fiscal_type}_max_nsu`,
  `{fiscal_type}_dfe_last_query`, etc. definidos pelos módulos específicos)
- **Modelos genéricos**: `l10n_br_fiscal_dfe.dfe` (payload XML por NSU) e
  `l10n_br_fiscal_dfe.document` (documento agrupado por chave de acesso)
- **Consulta manual** — assistente de busca específica por chave de acesso
  (com validação do dígito verificador) ou por NSU
- **Painel (banner)** genérico exibido nas visões dos módulos específicos
  via `banner_route`
- **Notificações no Inbox** — notifica usuários sobre novos documentos de
  terceiros (preferência por usuário)
- **Matching automático de parceiro** pelo CNPJ da chave de acesso
- **Log de distribuição** com request/response SOAP para depuração
- **Suporte multi-empresa** com record rules
- **Canal queue_job** `root.dfe` para as consultas automáticas
