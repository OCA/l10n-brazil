**Português** Integra l10n_br_account e l10n_br_nfse. Quando a fatura que
origina a NFS-e está em moeda estrangeira, os valores da NFS-e (serviços,
base, ISS, retenções, total recebido) são convertidos para reais pela taxa
da fatura (`invoice_currency_rate`, que já reflete a taxa manual do
account_manual_currency) na montagem dos dados enviados ao provedor, e os
dados de comércio exterior (moeda e valor na moeda original) são
preenchidos.

**English** Integrates l10n_br_account and l10n_br_nfse. When the invoice is
in a foreign currency, the NFS-e values are converted to reais with the
invoice rate when the provider data is built, and the foreign trade data
(currency and original amount) is filled in.
