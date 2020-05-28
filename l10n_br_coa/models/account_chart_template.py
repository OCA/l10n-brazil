# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


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
