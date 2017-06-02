# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models


class WizardMultiChartsAccounts(models.TransientModel):
    _inherit = 'wizard.multi.charts.accounts'

    transfer_account_id = fields.Many2one(
        required=False,
    )

    @api.onchange('chart_template_id')
    def onchange_chart_template_id(self):
        res = \
            super(WizardMultiChartsAccounts, self).onchange_chart_template_id()

        if self.chart_template_id:
            self.currency_id = self.chart_template_id.currency_id

        return res
