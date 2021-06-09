# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountTaxTemplate(models.Model):
    _name = "account.tax.template"
    _inherit = ["account.tax.mixin", "account.tax.template"]

    def _get_tax_vals(self, company, tax_template_to_tax):
        values = super()._get_tax_vals(company, tax_template_to_tax)
        values["deductible"] = self.deductible
        return values
