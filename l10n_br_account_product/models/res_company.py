# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

from .l10n_br_tax_definition_company_product import (
    L10nBrTaxDefinitionCompanyProduct
)


class ResCompany(models.Model):
    _inherit = 'res.company'

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

    nfe_version = fields.Selection(
        selection=[('1.10', '1.10'),
                   ('2.00', '2.00'),
                   ('3.10', '3.10'),
                   ('4.00', '4.00')],
        string=u'Versão NFe',
        required=True,
        default='4.00')

    nfe_import_folder = fields.Char(
        string=u'Pasta de Importação',
        size=254)

    nfe_export_folder = fields.Char(
        string=u'Pasta de Exportação',
        size=254)

    nfe_backup_folder = fields.Char(
        string=u'Pasta de Backup',
        size=254)

    nfe_environment = fields.Selection(
        selection=[('1', u'Produção'),
                   ('2', u'Homologação')],
        string=u'Ambiente Padrão',
        default='2')

    file_type = fields.Selection(
        selection=[('xml', 'XML')],
        string=u'Tipo do Arquivo Padrão',
        default='xml')

    sign_xml = fields.Boolean(
        string=u'Assinar XML')

    export_folder = fields.Boolean(
        string=u'Salvar na Pasta de Exportação')

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

    nfe_a1_file = fields.Binary(
        string=u'Arquivo NFe A1')

    nfe_a1_password = fields.Char(
        string=u'Senha NFe A1',
        size=64)

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

    accountant_cnpj_cpf = fields.Char(
        size=18,
        string=u'CNPJ/CPF Contador')


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
