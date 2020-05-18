# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountChartTemplate(models.Model):
    _inherit = 'account.chart.template'

    icms_sale_credit_id = fields.Many2one(
        comodel_name='account.account',
        string='Sale ICMS Credit Account',
    )
    icms_sale_debit_id = fields.Many2one(
        comodel_name='account.account',
        string='Sale ICMS Debit Account',
    )
    icms_st_sale_credit_id = fields.Many2one(
        comodel_name='account.account',
        string='Sale ICMS ST Credit Account',
    )
    icms_st_sale_debit_id = fields.Many2one(
        comodel_name='account.account',
        string='Sale ICMS ST Debit Account',
    )
    ipi_sale_credit_id = fields.Many2one(
        comodel_name='account.account',
        string='Sale IPI Credit Account',
    )
    ipi_sale_debit_id = fields.Many2one(
        comodel_name='account.account',
        string='Sale IPI Debit Account',
    )
    pis_sale_credit_id = fields.Many2one(
        comodel_name='account.account',
        string='Sale PIS Credit Account',
    )
    pis_sale_debit_id = fields.Many2one(
        comodel_name='account.account',
        string='Sale PIS Debit Account',
    )
    cofins_sale_credit_id = fields.Many2one(
        comodel_name='account.account',
        string='Sale COFINS Credit Account',
    )
    cofins_sale_debit_id = fields.Many2one(
        comodel_name='account.account',
        string='Sale COFINS Debit Account',
    )
    sale_revenue_credit_id = fields.Many2one(
        comodel_name='account.account',
        string='Sale Revenue Credit Account',
    )
    sale_revenue_debit_id = fields.Many2one(
        comodel_name='account.account',
        string='Sale Revenue Debit Account',
    )
    resale_revenue_credit_id = fields.Many2one(
        comodel_name='account.account',
        string='Resale Revenue Credit Account',
    )
    resale_revenue_debit_id = fields.Many2one(
        comodel_name='account.account',
        string='Resale Revenue Debit Account',
    )
    sale_st_revenue_credit_id = fields.Many2one(
        comodel_name='account.account',
        string='Sale ST Revenue Credit Account',
    )
    sale_st_revenue_debit_id = fields.Many2one(
        comodel_name='account.account',
        string='Sale ST Revenue Debit Account',
    )
    resale_st_revenue_credit_id = fields.Many2one(
        comodel_name='account.account',
        string='Resale ST Revenue Credit Account',
    )
    resale_st_revenue_debit_id = fields.Many2one(
        comodel_name='account.account',
        string='Resale ST Revenue Debit Account',
    )
    sale_return_credit_id = fields.Many2one(
        comodel_name='account.account',
        string='Sale Return Credit Account',
    )
    sale_return_debit_id = fields.Many2one(
        comodel_name='account.account',
        string='Sale Return Debit Account',
    )
    purchase_return_credit_id = fields.Many2one(
        comodel_name='account.account',
        string='Purchase Return Credit Account',
    )
    purchase_return_debit_id = fields.Many2one(
        comodel_name='account.account',
        string='Purchase Return Debit Account',
    )

    def try_loading_for_current_company(self):
        if self.currency_id == self.env.ref('base.BRL'):
            for template in \
                    self.env['l10n_br_account.tax.template'].search([]):
                template.create_account_tax_templates(self.id)
        return super(AccountChartTemplate, self
                     ).try_loading_for_current_company()
