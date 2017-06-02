# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models


class AccountChartTemplate(models.Model):
    _inherit = 'account.chart.template'

    is_brazilian_chart_template = fields.Boolean(
        string=u'Is a Brazilian chart_template?',
        compute='_compute_is_brazilian_chart_template',
    )
    sped_empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
    )
    transfer_account_id = fields.Many2one(
        required=False,
    )

    @api.depends('company_id', 'currency_id')
    def _compute_is_brazilian_chart_template(self):
        for chart_template in self:
            if chart_template.company_id.country_id:
                if chart_template.company_id.country_id.id == \
                        self.env.ref('base.br').id:
                    chart_template.is_brazilian_chart_template = True

                    #
                    # Brazilian chart templates, by law, must always be in BRL
                    #
                    chart_template.currency_id = self.env.ref('base.BRL').id

                    if chart_template.company_id.sped_empresa_id:
                        chart_template.sped_empresa_id = \
                            chart_template.company_id.sped_empresa_id.id

                    continue

            chart_template.is_brazilian_chart_template = False

    @api.onchange('sped_empresa_id')
    def _onchange_sped_empresa_id(self):
        self.ensure_one()
        self.company_id = self.sped_empresa_id.company_id

    @api.model
    def create(self, dados):
        if 'company_id' in dados:
            if 'sped_empresa_id' not in dados:
                company = self.env['res.company'].browse(dados['company_id'])

                if company.sped_empresa_id:
                    dados['sped_empresa_id'] = company.sped_empresa_id.id

        return super(AccountChartTemplate, self).create(dados)

    @api.one
    def try_loading_for_current_company(self):
        self.ensure_one()
        company = self.env.user.company_id
        # If we don't have any chart of account on this company, install this chart of account
        if not company.chart_template_id:
            wizard = self.env['wizard.multi.charts.accounts'].create({
                'company_id': self.env.user.company_id.id,
                'chart_template_id': self.id,
                'code_digits': self.code_digits,
                'transfer_account_id': self.transfer_account_id.id if self.transfer_account_id else False,
                'currency_id': self.currency_id.id,
                'bank_account_code_prefix': self.bank_account_code_prefix,
                'cash_account_code_prefix': self.cash_account_code_prefix,
            })
            wizard.onchange_chart_template_id()
            wizard.execute()

    @api.multi
    def _load_template(self, company, code_digits=None, transfer_account_id=None, account_ref=None, taxes_ref=None):
        """ Generate all the objects from the templates

            :param company: company the wizard is running for
            :param code_digits: number of digits the accounts code should have in the COA
            :param transfer_account_id: reference to the account template that will be used as intermediary account for transfers between 2 liquidity accounts
            :param acc_ref: Mapping between ids of account templates and real accounts created from them
            :param taxes_ref: Mapping between ids of tax templates and real taxes created from them
            :returns: tuple with a dictionary containing
                * the mapping between the account template ids and the ids of the real accounts that have been generated
                  from them, as first item,
                * a similar dictionary for mapping the tax templates and taxes, as second item,
            :rtype: tuple(dict, dict, dict)
        """
        self.ensure_one()
        if account_ref is None:
            account_ref = {}
        if taxes_ref is None:
            taxes_ref = {}
        if not code_digits:
            code_digits = self.code_digits
        if not transfer_account_id:
            transfer_account_id = self.transfer_account_id
        AccountTaxObj = self.env['account.tax']

        # Generate taxes from templates.
        generated_tax_res = self.tax_template_ids._generate_tax(company)
        taxes_ref.update(generated_tax_res['tax_template_to_tax'])

        # Generating Accounts from templates.
        account_template_ref = self.generate_account(taxes_ref, account_ref, code_digits, company)
        account_ref.update(account_template_ref)

        # writing account values after creation of accounts
        if transfer_account_id:
            company.transfer_account_id = account_template_ref[transfer_account_id.id]
        for key, value in generated_tax_res['account_dict'].items():
            if value['refund_account_id'] or value['account_id']:
                AccountTaxObj.browse(key).write({
                    'refund_account_id': account_ref.get(value['refund_account_id'], False),
                    'account_id': account_ref.get(value['account_id'], False),
                })

        # Create Journals - Only done for root chart template
        if not self.parent_id:
            self.generate_journals(account_ref, company)

        # generate properties function
        self.generate_properties(account_ref, company)

        # Generate Fiscal Position , Fiscal Position Accounts and Fiscal Position Taxes from templates
        self.generate_fiscal_position(taxes_ref, account_ref, company)

        # Generate account operation template templates
        self.generate_account_reconcile_model(taxes_ref, account_ref, company)

        return account_ref, taxes_ref
