# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

from .constants.fiscal import TAX_FRAMEWORK, TAX_FRAMEWORK_DEFAULT


class ResCompany(models.Model):
    _inherit = 'res.company'

    cnae_main_id = fields.Many2one(
        comodel_name='fiscal.cnae',
        domain="[('internal_type', '=', 'normal'), "
               "('id', 'not in', cnae_secondary_ids)]",
        string='Main CNAE')

    cnae_secondary_ids = fields.Many2many(
        comodel_name='fiscal.cnae',
        relation='res_company_fiscal_cnae_rel',
        colunm1='company_id',
        colunm2='cnae_id',
        domain="[('internal_type', '=', 'normal'), "
               "('id', '!=', cnae_main_id)]",
        string='Secondary CNAE')

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        default=TAX_FRAMEWORK_DEFAULT,
        string='Tax Framework')

    annual_revenue = fields.Monetary(
        string='Annual Revenue',
        currency_field='currency_id',
        default=0.00,
        digits=dp.get_precision('Fiscal Documents'))

    simplifed_tax_id = fields.Many2one(
        comodel_name='fiscal.simplified.tax',
        domain="[('cnae_ids', '=', cnae_main_id)]",
        string='Simplified Tax')

    ibpt_token = fields.Char(
        string=u'IPBT Token')

    ibpt_update_days = fields.Integer(
        string=u'IPBT Token Updates')

    certificate_ecnpj_id = fields.Many2one(
        comodel_name='fiscal.certificate',
        string='E-CNPJ',
        domain="[('type', '=', 'e-cnpj'), ('is_valid', '=', True)]")

    certificate_nfe_id = fields.Many2one(
        comodel_name='fiscal.certificate',
        string='NFe',
        domain="[('type', '=', 'nf-e'), ('is_valid', '=', True)]")

    accountant_id = fields.Many2one(
        comodel_name='res.partner',
        string='Accountant')

"""
    @api.one
    @api.depends('product_tax_definition_line.tax_id')
    def _compute_taxes(self):
        product_taxes = self.env['account.tax']
        for tax in self.product_tax_definition_line:
            product_taxes += tax.tax_id
        self.product_tax_ids = product_taxes

    product_invoice_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.document',
        string=u'Documento Fiscal')

    document_serie_product_ids = fields.Many2many(
        comodel_name='l10n_br_account.document.serie',
        relation='res_company_l10n_br_account_document_serie',
        column1='company_id',
        column2='document_serie_product_id',
        string=u'Série de Documentos Fiscais',
        domain="[('company_id', '=', active_id),('active','=',True),"
               "('fiscal_type','=','product')]")

    product_tax_definition_line = fields.One2many(
        comodel_name='l10n_br_tax.definition.company.product',
        inverse_name='company_id',
        string=u'Taxes Definitions')

    product_tax_ids = fields.Many2many(
        comodel_name='account.tax',
        string=u'Product Taxes',
        compute='_compute_taxes',
        store=True)

    in_invoice_fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Categoria Fiscal de Produto Padrão de Entrada',
        domain="[('journal_type','=','purchase'),"
               " ('state', '=', 'approved'), ('fiscal_type','=','product'),"
               " ('type','=','input')]")

    out_invoice_fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Categoria Fiscal de Produto Padrão de Saida',
        domain="[('journal_type','=','sale'), ('state', '=', 'approved'),"
               " ('fiscal_type','=','product'), ('type','=','output')]")

    in_refund_fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Devolução Entrada',
        domain="[('journal_type','=','purchase_refund'),"
               "('state', '=', 'approved'), ('fiscal_type','=','product'),"
               "('type','=','output')]")

    out_refund_fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Devolução Saida',
        domain="[('journal_type','=','sale_refund'),"
               "('state', '=', 'approved'), ('fiscal_type','=','product'),"
               " ('type','=','input')]")

    freight_tax_id = fields.Many2one(
        comodel_name='account.tax',
        string=u'Freight Sale Tax',
        domain=[('domain', '=', 'freight')])

    insurance_tax_id = fields.Many2one(
        comodel_name='account.tax',
        string=u'Insurance Sale Tax',
        domain=[('domain', '=', 'insurance')])

    other_costs_tax_id = fields.Many2one(
        comodel_name='account.tax',
        string=u'Other Costs Sale Tax',
        domain=[('domain', '=', 'other_costs')])


class L10nBrTaxDefinitionCompanyProduct(L10nBrTaxDefinitionCompanyProduct,
                                        models.Model):
    _name = 'l10n_br_tax.definition.company.product'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string=u'Empresa')

    _sql_constraints = [
        ('l10n_br_tax_definition_tax_id_uniq',
         'unique (tax_id, company_id)',
         u'Imposto já existente nesta empresa!')]
"""
