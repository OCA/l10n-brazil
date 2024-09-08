# Copyright 2024 Marcel Savegnago - Escodoo (https://www.escodoo.com.br)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FiscalTaxGroup(models.Model):
    _inherit = "l10n_br_fiscal.tax.group"

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Account Journal",
        company_dependent=True,
        domain="[('type', '=', 'purchase')]",
    )

    generate_wh_invoice = fields.Boolean(
        string="Generate WH Invoice",
        default=False,
        company_dependent=True,
    )
