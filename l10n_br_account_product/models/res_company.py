# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api

from openerp.addons.l10n_br_account.models.l10n_br_account import (
    L10nBrTaxDefinition
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
        'l10n_br_account.fiscal.document', 'Documento Fiscal')
    document_serie_product_ids = fields.Many2many(
        'l10n_br_account.document.serie',
        'res_company_l10n_br_account_document_serie', 'company_id',
        'document_serie_product_id', 'Série de Documentos Fiscais',
        domain="[('company_id', '=', active_id),('active','=',True),"
        "('fiscal_type','=','product')]")
    nfe_version = fields.Selection(
        [('1.10', '1.10'), ('2.00', '2.00'), ('3.10', '3.10')], u'Versão NFe',
        required=True, default='3.10')
    nfe_import_folder = fields.Char('Pasta de Importação', size=254)
    nfe_export_folder = fields.Char('Pasta de Exportação', size=254)
    nfe_backup_folder = fields.Char('Pasta de Backup', size=254)
    nfe_environment = fields.Selection(
        [('1', u'Produção'), ('2', u'Homologação')], 'Ambiente Padrão')
    file_type = fields.Selection(
        [('xml', 'XML'), ('txt', ' TXT')], 'Tipo do Arquivo Padrão')
    sign_xml = fields.Boolean('Assinar XML')
    export_folder = fields.Boolean(u'Salvar na Pasta de Exportação')
    product_tax_definition_line = fields.One2many(
        'l10n_br_tax.definition.company.product',
        'company_id', 'Taxes Definitions')
    product_tax_ids = fields.Many2many(
        'account.tax', string='Product Taxes', compute='_compute_taxes',
        store=True)
    in_invoice_fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        'Categoria Fiscal de Produto Padrão de Entrada',
        domain="[('journal_type','=','purchase'),"
        " ('state', '=', 'approved'), ('fiscal_type','=','product'),"
        " ('type','=','input')]")
    out_invoice_fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        'Categoria Fiscal de Produto Padrão de Saida',
        domain="[('journal_type','=','sale'), ('state', '=', 'approved'),"
        " ('fiscal_type','=','product'), ('type','=','output')]")
    in_refund_fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Devolução Entrada',
        domain="[('journal_type','=','purchase_refund'),"
        "('state', '=', 'approved'), ('fiscal_type','=','product'),"
        "('type','=','output')]")
    out_refund_fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Devolução Saida',
        domain="[('journal_type','=','sale_refund'),"
        "('state', '=', 'approved'), ('fiscal_type','=','product'),"
        " ('type','=','input')]")
    nfe_a1_file = fields.Binary('Arquivo NFe A1')
    nfe_a1_password = fields.Char('Senha NFe A1', size=64)
    freight_tax_id = fields.Many2one(
        'account.tax', string='Freight Sale Tax',
        domain=[('domain', '=', 'freight')])
    insurance_tax_id = fields.Many2one(
        'account.tax', string='Insurance Sale Tax',
        domain=[('domain', '=', 'insurance')])
    other_costs_tax_id = fields.Many2one(
        'account.tax', string='Other Costs Sale Tax',
        domain=[('domain', '=', 'other_costs')])
    accountant_cnpj_cpf = fields.Char(size=18, string='CNPJ/CPF Contador')


class L10nBrTaxDefinitionCompanyProduct(L10nBrTaxDefinition, models.Model):
    _name = 'l10n_br_tax.definition.company.product'

    company_id = fields.Many2one('res.company', 'Empresa')
    tax_ipi_guideline_id = fields.Many2one(
        'l10n_br_account_product.ipi_guideline', string=u'Enquadramento IPI')
    tax_icms_relief_id = fields.Many2one(
        'l10n_br_account_product.icms_relief', string=u'Desoneração ICMS')

    _sql_constraints = [
        ('l10n_br_tax_definition_tax_id_uniq',
         'unique (tax_id, company_id)',
         u'Imposto já existente nesta empresa!')
    ]
