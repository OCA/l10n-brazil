# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

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

    def account_tax_group(self):
        self.ensure_one()
        return self.env["account.tax.group"].search(
            [("fiscal_tax_group_id", "in", self.ids)], limit=1
        )
