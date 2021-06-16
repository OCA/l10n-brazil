# Copyright 2021 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Cfop(models.Model):

    _inherit = "l10n_br_fiscal.cfop"

    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Account",
        company_dependent=True,
    )
