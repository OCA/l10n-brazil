# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountChartTemplate(models.Model):
    _inherit = 'account.chart.template'

    def try_loading_for_current_company(self):
        if self.currency_id == self.env.ref('base.BRL'):
            for template in \
                    self.env['l10n_br_account.tax.template'].search([]):
                template.create_account_tax_templates(self.id)
        return super(AccountChartTemplate, self
                     ).try_loading_for_current_company()
