# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    is_brazilian_chart_template = fields.Boolean(
        string=u'Is a Brazilian chart_template?',
    )

    @api.onchange('chart_template_id')
    def onchange_chart_template_id(self):
        res = super(AccountConfigSettings, self).onchange_chart_template_id()

        self.is_brazilian_chart_template = \
            self.chart_template_id.is_brazilian_chart_template

        if self.is_brazilian_chart_template:
            self.currency_id = self.env.ref('base.BRL').id
        elif self.chart_template_id:
            self.currency_id = self.chart_template_id.currency_id

        return res

    @api.multi
    def set_chart_of_accounts(self):
        if not self.is_brazilian_chart_template:
            return super(AccountConfigSettings, self).set_chart_of_accounts()

        if self.chart_template_id and not self.has_chart_of_accounts and \
                self.expects_chart_of_accounts:
            if self.company_id.chart_template_id and \
                self.chart_template_id != self.company_id.chart_template_id:
                raise UserError(_('You can not change a company chart of account once it has been installed'))

            wizard = self.env['wizard.multi.charts.accounts'].create({
                'company_id': self.company_id.id,
                'chart_template_id': self.chart_template_id.id,
                'transfer_account_id': self.template_transfer_account_id.id,
                'code_digits': self.code_digits or 6,
                'sale_tax_id': self.sale_tax_id.id,
                'purchase_tax_id': self.purchase_tax_id.id,
                'sale_tax_rate': self.sale_tax_rate,
                'purchase_tax_rate': self.purchase_tax_rate,
                'complete_tax_set': self.complete_tax_set,
                'currency_id': self.currency_id.id,
                'bank_account_code_prefix': self.bank_account_code_prefix or self.chart_template_id.bank_account_code_prefix,
                'cash_account_code_prefix': self.cash_account_code_prefix or self.chart_template_id.cash_account_code_prefix,
                'is_brazilian_chart_template': self.is_brazilian_chart_template,
            })
            wizard.execute()