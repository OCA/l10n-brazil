# Monitor de NFS-e nacional (Distribuição DF-e)

Este módulo baixa as **NFS-e nacionais** emitidas contra o CNPJ da empresa pela API de distribuição do ADN (Ambiente de Dados Nacional) e as coloca na mesma caixa de entrada do monitor de DF-e.

A NF-e continua no webservice SOAP `NFeDistribuicaoDFe`. A NFS-e nacional usa um cliente REST com certificado digital (mTLS) e não passa por esse fluxo.

## Principais funcionalidades

* Consulta por NSU em `GET /contribuintes/DFe/{NSU}`, com paginação do lote.
* Gravação em `l10n_br_fiscal_dfe.document` e `l10n_br_fiscal_dfe.dfe`, com o tipo fiscal `nfse`.
* Notas completas e eventos. O cancelamento atualiza a situação do documento já recebido.
* Importação do XML nacional como documento fiscal de serviço (modelo `SE`), com uma linha de serviço.
* Cron e canal `queue_job` reutilizados pelo motor genérico de DF-e.
