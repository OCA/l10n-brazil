# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

from ..constants.fiscal import TAX_FRAMEWORK, TAX_FRAMEWORK_DEFAULT


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def _compute_l10n_br_data(self):
        """ Read the l10n_br specific functional fields. """
        super(ResCompany, self)._compute_l10n_br_data()
        for c in self:
            c.tax_framework = c.partner_id.tax_framework
            c.cnae_main_id = c.partner_id.cnae_main_id

    def _inverse_cnae_main_id(self):
        """ Write the l10n_br specific functional fields. """
        for c in self:
            c.partner_id.cnae_main_id = c.cnae_main_id

    def _inverse_tax_framework(self):
        """ Write the l10n_br specific functional fields. """
        for c in self:
            c.partner_id.tax_framework = c.tax_framework

    @api.one
    @api.depends('simplifed_tax_id', 'annual_revenue')
    def _compute_simplifed_tax_range(self):
        range = self.env['l10n_br_fiscal.simplified.tax.range'].search(
            [('inital_revenue', '<=', self.annual_revenue),
             ('final_revenue', '>=', self.annual_revenue)],
            limit=1)

        if range:
            self.simplifed_tax_range_id = range.id

    cnae_main_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cnae',
        compute='_compute_l10n_br_data',
        inverse='_inverse_cnae_main_id',
        domain="[('internal_type', '=', 'normal'), "
               "('id', 'not in', cnae_secondary_ids)]",
        string='Main CNAE')

    cnae_secondary_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.cnae',
        relation='res_company_fiscal_cnae_rel',
        colunm1='company_id',
        colunm2='cnae_id',
        domain="[('internal_type', '=', 'normal'), "
               "('id', '!=', cnae_main_id)]",
        string='Secondary CNAE')

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        default=TAX_FRAMEWORK_DEFAULT,
        compute='_compute_l10n_br_data',
        inverse='_inverse_tax_framework',
        string='Tax Framework')

    annual_revenue = fields.Monetary(
        string='Annual Revenue',
        currency_field='currency_id',
        default=0.00,
        digits=dp.get_precision('Fiscal Documents'))

    simplifed_tax_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.simplified.tax',
        domain="[('cnae_ids', '=', cnae_main_id)]",
        string='Simplified Tax')

    simplifed_tax_range_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.simplified.tax.range',
        domain="[('simplified_tax_id', '=', simplifed_tax_id)]",
        compute='_compute_simplifed_tax_range',
        store=True,
        readyonly=True,
        string='Simplified Tax Range')

    simplifed_tax_percent = fields.Float(
        string='Simplifed Tax Percent',
        default=0.00,
        related='simplifed_tax_range_id.total_tax_percent',
        digits=dp.get_precision('Fiscal Tax Percent'))

    ibpt_api = fields.Boolean(
        string='Use IBPT API',
        default=False)

    ibpt_token = fields.Char(
        string='IPBT Token')

    ibpt_update_days = fields.Integer(
        string='IPBT Token Updates',
        default=15)

    certificate_ecnpj_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.certificate',
        string='E-CNPJ',
        domain="[('type', '=', 'e-cnpj'), ('is_valid', '=', True)]")

    certificate_nfe_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.certificate',
        string='NFe',
        domain="[('type', '=', 'nf-e'), ('is_valid', '=', True)]")

    accountant_id = fields.Many2one(
        comodel_name='res.partner',
        string='Accountant')

    @api.onchange('cnae_main_id')
    def _onchange_cnae_main_id(self):
        simplified_tax = self.env['l10n_br_fiscal.simplified.tax'].search(
            [('cnae_ids', '=', self.cnae_main_id.id)],
            limit=1)

        if simplified_tax:
            self.simplifed_tax_id = simplified_tax.id

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
