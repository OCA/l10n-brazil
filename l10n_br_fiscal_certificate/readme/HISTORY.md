## 18.0.2.0.0 (2026)

Reaproveitamento do módulo nativo `certificate`: o modelo próprio
`l10n_br_fiscal.certificate` foi substituído por uma extensão de
`certificate.certificate` e os campos `certificate_nfe_id` e
`certificate_ecnpj_id` da empresa por um único `certificate_id`. Os campos
`type` e `subtype` (NF-e / e-CNPJ) deixaram de existir: agora a empresa tem um
único certificado, marcado com o escopo `l10n_br`. Uma migração converte os
certificados existentes para o modelo nativo.

## 14.0.1.0.0 (2023)

Primeira versão do módulo: o código vinha sendo desenvolvido desde a
versão 8 mas estava integrado dentro módulo l10n_br_fiscal. O código foi
extraído para deixar o módulo l10n_br_fiscal mais leve.
