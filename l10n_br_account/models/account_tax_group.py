# Copyright (C) 2009  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class AccountTaxGroup(models.Model):
    _inherit = "account.tax.group"

    fiscal_tax_group_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.group",
        string="Fiscal Tax Group",
    )

    def deductible_tax(self, type_tax_use="sale"):
        return self.env["account.tax"].search(
            [
                ("type_tax_use", "=", type_tax_use),
                ("tax_group_id", "=", self.id),
                ("deductible", "=", True),
                ("company_id", "=", self.env.user.company_id.id),
            ],
            limit=1,
        )
