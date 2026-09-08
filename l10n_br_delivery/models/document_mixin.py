# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FiscalDocumentMixin(models.AbstractModel):
    _inherit = "l10n_br_fiscal.document.mixin"

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Carrier",
        ondelete="restrict",
    )
