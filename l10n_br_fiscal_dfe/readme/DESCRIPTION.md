Módulo para monitoramento de NF-e recebidas via o web service de
Distribuição de DF-e da SEFAZ (NFeDistribuicaoDFe — Ambiente Nacional),
implementado conforme a
[Nota Técnica 2014.002 v1.30](https://www.nfe.fazenda.gov.br/portal/exibirArquivo.aspx?conteudo=P0U3lU1Fe40=).

Permite que empresas consultem automaticamente todos os documentos fiscais
eletrônicos emitidos contra seu CNPJ, sem necessidade de receber o XML
diretamente do emissor.

Principais funcionalidades:

- **Consulta automática** via cron com `queue_job` — paginação de NSUs,
  agendamento inteligente baseado na resposta da SEFAZ (138, 137, 656)
- **Consulta manual** — busca geral ou específica (por chave de acesso ou NSU)
- **Processamento de 4 schemas XML**: `procNFe` (NF-e completa), `resNFe`
  (resumo), `resEvento` e `procEventoNFe`
- **Importação de NF-e** — cria `l10n_br_fiscal.document` a partir do XML
  completo
- **Geração de DANFE** em PDF via `brazilfiscalreport`
- **Download de XMLs** — individual ou em lote (zip)
- **Manifestação automática** do destinatário (ciência da operação)
- **Dashboard** com status da distribuição, progresso de NSU, alertas de
  inatividade e documentos pendentes de importação
- **Notificações no Inbox** — notifica usuários sobre novos documentos de
  terceiros
- **Matching automático de parceiro** pelo CNPJ da chave de acesso
- **Suporte multi-empresa** com record rules e configuração por empresa
- **Log de distribuição** com request/response SOAP para depuração
