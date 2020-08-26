# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountChartTemplate(models.Model):
    _inherit = 'account.chart.template'

    def try_loading_for_current_company(self):
        self.ensure_one()
        if self.currency_id == self.env.ref('base.BRL'):
            for template in \
                    self.env['l10n_br_account.tax.template'].search([]):
                template.create_account_tax_templates(self.id)
        return super().try_loading_for_current_company()

    def load_for_current_company(self, sale_tax_rate, purchase_tax_rate):
        super().load_for_current_company(sale_tax_rate, purchase_tax_rate)
        # Remove Company default taxes configuration
        if self.currency_id == self.env.ref('base.BRL'):
            self.env.user.company_id.write({
                'account_sale_tax_id': False,
                'account_purchase_tax_id': False,
            })
