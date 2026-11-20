## Canal queue_job

As consultas rodam no canal `root.dfe` do framework base, que deve ter capacidade de **1 job simultâneo** (ver `l10n_br_fiscal_dfe`).

## Configuração da empresa

Em **Faturamento > Configuração > Empresas**, aba **Fiscal > CT-e DF-e**:

- **Ambiente CT-e**: Produção ou Homologação (o mesmo usado pela emissão de CT-e).
- **Busca automática de CT-e DF-e**: habilita a consulta periódica via cron.

O último NSU, o NSU máximo e o status da última consulta ficam visíveis na mesma aba.
