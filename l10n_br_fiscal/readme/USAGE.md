Você pode criar documentos fiscais direitamente pelo menu fiscal, mas a
princípio você vai pilotar a criação de documentos fiscais a partir dos
invoices Odoo, usando módulos adicionais como l10n_br_account,
l10n_br_sale, l10n_br_purchase...

Na maioria dos leiautes de NFS-e a nota declara um único serviço. Um
documento de serviço emitido pela empresa só é confirmado quando todas as
linhas têm o mesmo item da LC 116, códigos de tributação, NBS, local da
prestação, exigibilidade e alíquotas do ISS (inclusive a retenção) e
classificação e CST do IBS e da CBS. Caso contrário, a confirmação é
recusada e a mensagem lista as linhas de cada serviço. Documentos de
fornecedor não passam por essa conferência.
