# Copyright (C) 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class DocumentLineMixin(models.AbstractModel):
    _inherit = "l10n_br_fiscal.document.line.mixin"

    afrmm_value = fields.Monetary(
        string="AFRMM",
        help="Additional Freight for Renewal of the Merchant Marine, "
        "allocated to this line from the total amount reported by the "
        "DUIMP.",
    )

    @api.model
    def _add_fields_to_amount(self):
        fields_to_amount = super()._add_fields_to_amount()
        fields_to_amount.append("afrmm_value")
        return fields_to_amount
