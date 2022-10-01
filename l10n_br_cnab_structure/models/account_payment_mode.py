# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models


class AccountPaymentMode(models.Model):
    """
    Override Account Payment Mode
    """

    _inherit = "account.payment.mode"

    cnab_processor = fields.Selection(
        selection_add=[("oca_processor", "OCA Processor")],
    )

    cnab_structure_id = fields.Many2one("l10n_br_cnab.structure")
