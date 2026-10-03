This module extends the Odoo Repair module to adapt it to the Brazilian
needs. Since Odoo 17.0 the repair order is billed through a sale order:
this module sets the fiscal operation of the repair order and carries it
to the quotation created from the repair and to the lines of the repair
parts, so the Brazilian taxes are computed and the fiscal documents
(NF-e, NFS-e and others) are issued by the Brazilian sale localization
(l10n_br_sale).
