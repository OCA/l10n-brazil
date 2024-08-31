from odoo import models


class FiscalDocumentMixin(models.AbstractModel):
    _name = "l10n_br_fiscal.document.mixin"
    _inherit = [
        "l10n_br_fiscal.document.mixin.fields",
        "l10n_br_fiscal.document.mixin.methods",
    ]
    _description = "Document Fiscal Mixin"
