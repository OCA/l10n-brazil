# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResPartner(models.Model):
    """What the EFD-Reinf needs to know about a beneficiary.

    Only what really belongs to the person, and not what belongs to the
    payment: the nature of income here is a fallback for what has no service
    type, never the source of truth.

    The Simples Nacional is not repeated here: the localization already keeps
    it in tax_framework, and a second place to say the same thing is a second
    place to get it wrong.
    """

    _inherit = "res.partner"

    reinf_nature_income_id = fields.Many2one(
        comodel_name="l10n_br_reinf.nature.income",
        string="EFD-Reinf Nature of Income",
        help="Fallback nature of income for payments to this partner that have "
        "no service type to take it from.",
    )
