# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class AccountTaxTemplate(models.Model):
    _inherit = "account.tax.template"

    fiscal_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax",
        relation="fiscal_account_template_tax_rel",
        column1="account_tax_template_id",
        column2="fiscal_tax_id",
        string="Fiscal Taxes",
    )

    def _generate_tax(self, company):
        mapping = super()._generate_tax(company)
        taxes_template = self.browse(mapping.get("tax_template_to_tax").keys())

        for tax_template in taxes_template:
            tax_id = mapping.get("tax_template_to_tax").get(tax_template.id)
            self.env["account.tax"].browse(tax_id).write(
                {"fiscal_tax_ids": [(6, False, tax_template.fiscal_tax_ids.ids)]}
            )

        return mapping
