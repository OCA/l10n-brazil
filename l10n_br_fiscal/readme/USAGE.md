Você pode criar documentos fiscais direitamente pelo menu fiscal, mas a
princípio você vai pilotar a criação de documentos fiscais a partir dos
invoices Odoo, usando módulos adicionais como l10n_br_account,
l10n_br_sale, l10n_br_purchase...

Ao trocar o regime tributário ou um imposto padrão da empresa (aba Fiscal),
as definições tributárias genéricas da empresa acompanham a troca: a
definição antiga fica Expirada, com a data de fim, e a nova começa na data
da gravação. As definições com condição (NCM, produto, estado de destino
etc.) não mudam. O antes e o depois ficam registrados numa nota no contato
da empresa.
