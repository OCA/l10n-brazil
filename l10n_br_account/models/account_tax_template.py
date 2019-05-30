# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api


class AccountTaxTemplate(models.Model):
    _name = 'account.tax.template'
    _inherit = ['account.tax.fiscal.abstract', 'account.tax.template']

    @api.multi
    def _generate_tax(self, company):
        mapping = super(AccountTaxTemplate, self)._generate_tax(company)

        taxes_template = self.browse(
            mapping.get('tax_template_to_tax').keys())

        for tax_template in taxes_template:
            tax_id = mapping.get('tax_template_to_tax').get(tax_template.id)
            self.env['account.tax'].browse(tax_id).write(
                {'fiscal_tax_id': tax_template.fiscal_tax_id.id})

        return mapping
