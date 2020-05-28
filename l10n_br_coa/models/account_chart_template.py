# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountChartTemplate(models.Model):
    _inherit = 'account.chart.template'

    icms_sale_credit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Sale ICMS Credit Account',
    )
    icms_sale_debit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Sale ICMS Debit Account',
    )
    icms_st_sale_credit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Sale ICMS ST Credit Account',
    )
    icms_st_sale_debit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Sale ICMS ST Debit Account',
    )
    ipi_sale_credit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Sale IPI Credit Account',
    )
    ipi_sale_debit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Sale IPI Debit Account',
    )
    pis_sale_credit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Sale PIS Credit Account',
    )
    pis_sale_debit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Sale PIS Debit Account',
    )
    cofins_sale_credit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Sale COFINS Credit Account',
    )
    cofins_sale_debit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Sale COFINS Debit Account',
    )
    sale_revenue_credit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Sale Revenue Credit Account',
    )
    sale_revenue_debit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Sale Revenue Debit Account',
    )
    resale_revenue_credit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Resale Revenue Credit Account',
    )
    resale_revenue_debit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Resale Revenue Debit Account',
    )
    sale_st_revenue_credit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Sale ST Revenue Credit Account',
    )
    sale_st_revenue_debit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Sale ST Revenue Debit Account',
    )
    resale_st_revenue_credit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Resale ST Revenue Credit Account',
    )
    resale_st_revenue_debit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Resale ST Revenue Debit Account',
    )
    sale_return_credit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Sale Return Credit Account',
    )
    sale_return_debit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Sale Return Debit Account',
    )
    purchase_return_credit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Purchase Return Credit Account',
    )
    purchase_return_debit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Purchase Return Debit Account',
    )

    simple_national_credit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Simple National Credit Account',
    )

    simple_national_debit_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Simple National Debit Account',
    )

    def load_for_current_company(self, sale_tax_rate, purchase_tax_rate):
        super().load_for_current_company(sale_tax_rate, purchase_tax_rate)
        # Remove Company default taxes configuration
        if self.currency_id == self.env.ref('base.BRL'):
            self.env.user.company_id.write({
                'account_sale_tax_id': False,
                'account_purchase_tax_id': False,
            })

    @api.multi
    def _load_template(self, company, code_digits=None,
                       account_ref=None, taxes_ref=None):
        account_ref, taxes_ref = super()._load_template(
            company, code_digits, account_ref, taxes_ref
        )

        if self.parent_id:
            chart_template_ref = self.get_external_id().get(self.id)
            coa_name, _ = chart_template_ref.split('.')
            coa_name = coa_name + '_'
            acc_names = {
                'sale': {
                    'account_id': 'account_id',
                    'refund_account_id': 'refund_account_id'},
                'purchase': {
                    'account_id': 'refund_account_id',
                    'refund_account_id': 'account_id'},
                'all': {
                    'account_id': 'account_id',
                    'refund_account_id': 'refund_account_id'},
            }

            properties = self.env['ir.property'].search([
                ('name', 'ilike', coa_name + '%'),
                ('company_id', '=', False),
                ('type', '=', 'many2one'),
                ('res_id', 'ilike', 'account.tax.group,%'),
            ])

            group_accounts = {
                int(p.res_id.split(',')[1]): {} for p in properties}

            for property in properties:
                group_accounts[int(property.res_id.split(',')[1])].update({
                    property.fields_id.name:
                    account_ref.get(
                        (int(property.value_reference.split(',')[1])), False)
                })

            taxes = self.env['account.tax'].browse(taxes_ref.values())
            for tax in taxes:
                group_account = group_accounts.get(tax.tax_group_id.id, {})
                if group_account:
                    if tax.deductible:
                        account_id = group_account.get('ded_account_id')
                        refund_account_id = group_account.get(
                            'ded_refund_account_id')
                    else:
                        account_id = group_account.get(
                            acc_names.get(tax.type_tax_use, {}).get(
                                'account_id'))
                        refund_account_id = group_account.get(
                            acc_names.get(tax.type_tax_use, {}).get(
                                'refund_account_id'))

                    tax.write({
                        'account_id': account_id,
                        'refund_account_id': refund_account_id,
                    })

        return account_ref, taxes_ref
