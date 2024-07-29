# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from odoo.addons.l10n_br_account_payment_order.models.account_payment_line import (
    AccountPaymentLine,
)


class CNABTPixransferType(models.Model):
    """CNAB Pix Transfer Type"""

    _name = "cnab.pix.transfer.type"
    _description = "CNAB Pix Transfer Type"

    name = fields.Char(compute="_compute_name")
    code = fields.Char(required=True)
    description = fields.Char()

    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
        string="Cnab Structure",
        ondelete="cascade",
        required=True,
    )

    type_domain = fields.Selection(
        selection=AccountPaymentLine.PIX_TRANSFER_TYPES,
        string="Transfer Type",
    )

    @api.depends("code", "name")
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.code} - {rec.description}"
