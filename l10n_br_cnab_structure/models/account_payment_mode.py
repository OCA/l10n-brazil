# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class AccountPaymentMode(models.Model):
    """
    Override Account Payment Mode
    """

    _inherit = "account.payment.mode"

    cnab_structure_id = fields.Many2one("l10n_br_cnab.structure")

    cnab_payment_way_ids = fields.Many2many(
        comodel_name="cnab.payment.way",
        relation="payment_mode_cnab_payment_way_rel",
        string="CNAB Payment Ways",
    )

    cnab_structure_ok = fields.Boolean(
        string="Allowed in CNAB (OCA Processor)", default=False
    )

    @api.model
    def _selection_cnab_processor(self):
        selection = super()._selection_cnab_processor()
        selection.append(("oca_processor", "OCA Processor"))
        return selection
