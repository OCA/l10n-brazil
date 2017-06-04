# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

_logger = logging.getLogger(__name__)

from odoo.exceptions import AccessError
from odoo import api, fields, models, _


class WizardMultiChartsAccounts(models.TransientModel):
    _inherit = 'wizard.multi.charts.accounts'

    is_brazilian_chart_template = fields.Boolean(
        string=u'Is a Brazilian chart_template?',
    )
    transfer_account_id = fields.Many2one(
        required=False,
    )

    @api.onchange('chart_template_id')
    def onchange_chart_template_id(self):
        res = \
            super(WizardMultiChartsAccounts, self).onchange_chart_template_id()

        self.is_brazilian_chart_template = \
            self.chart_template_id.is_brazilian_chart_template

        if self.is_brazilian_chart_template:
            self.currency_id = self.env.ref('base.BRL').id
        elif self.chart_template_id:
            self.currency_id = self.chart_template_id.currency_id

        return res

    @api.multi
    def execute(self):
        if not self.is_brazilian_chart_template:
            return super(WizardMultiChartsAccounts, self).execute()

        if not self.env.user._is_admin():
            raise AccessError(_("Only administrators can change the settings"))

        #
        # Ativa o Real R$
        #
        self.currency_id.write({'active': True})

        #
        # O plano de contas no Brasil deve ser único para todas as empresas
        # do banco de dados, não deve haver casos em que empresas do mesmo
        # CNPJ usem planos de contas diferentes;
        # Portanto, a não ser em casos de multicompany REAL (coisa que vamos
        # evitar), deve haver somente 1 plano de contas no sistema
        #
        if len(self.env['account.account'].search([])) > 0:
            _logger.info('Já existe um plano de contas instalado, ignorando.')
            return {}

        company = self.company_id
        company.write({
            'currency_id': self.env.ref('base.BRL').id,
            'country_id': self.env.ref('base.br').id,
            'accounts_code_digits': self.code_digits,
            'anglo_saxon_accounting': self.use_anglo_saxon,
            'bank_account_code_prefix': self.bank_account_code_prefix,
            'cash_account_code_prefix': self.cash_account_code_prefix,
            'chart_template_id': self.chart_template_id.id,
        })

        #
        # Setamos todos as definições de listas de preços em Real R$
        #
        if company.id == 1:
            for reference in ['product.list_price', 'product.standard_price',
                              'product.list0']:
                try:
                    lista_pool = self.env.ref(reference)
                    lista_pool.write({'currency_id': self.currency_id.id})
                except ValueError:
                    pass

        # # If the floats for sale/purchase rates have been filled, create templates from them
        # self._create_tax_templates_from_rates(company.id)

        # Install all the templates objects and generate the real objects
        acc_template_ref, taxes_ref = \
            self.chart_template_id._install_template(company,
                code_digits=self.code_digits,
                transfer_account_id=self.transfer_account_id)

        # # write values of default taxes for product as super user
        # ir_values_pool = self.env['ir.values']
        # if self.sale_tax_id and taxes_ref:
        #     ir_values_pool.sudo().set_default('product.template', "taxes_id", [taxes_ref[self.sale_tax_id.id]], for_all_users=True, company_id=company.id)
        # if self.purchase_tax_id and taxes_ref:
        #     ir_values_pool.sudo().set_default('product.template', "supplier_taxes_id", [taxes_ref[self.purchase_tax_id.id]], for_all_users=True, company_id=company.id)

        # # Create Bank journals
        # self._create_bank_journals_from_o2m(company, acc_template_ref)
        #
        # # Create the current year earning account if it wasn't present in the CoA
        # account_obj = self.env['account.account']
        # unaffected_earnings_xml = self.env.ref("account.data_unaffected_earnings")
        # if unaffected_earnings_xml and not account_obj.search([('company_id', '=', company.id), ('user_type_id', '=', unaffected_earnings_xml.id)]):
        #     account_obj.create({
        #         'code': '999999',
        #         'name': _('Undistributed Profits/Losses'),
        #         'user_type_id': unaffected_earnings_xml.id,
        #         'company_id': company.id,})

        return {}
