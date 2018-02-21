# -*- coding: utf-8 -*-
# Copyright (C) 2012  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api
from openerp.addons import decimal_precision as dp


class AccountProductFiscalClassificationTemplate(models.Model):
    _inherit = 'account.product.fiscal.classification.template'
    _rec_name = 'code'

    @api.multi
    @api.depends('purchase_tax_definition_line',
                 'sale_tax_definition_line')
    def _compute_taxes(self):
        for fc in self:
            fc.sale_tax_ids = [line.tax_template_id.id for line in
                               fc.sale_tax_definition_line]
            fc.purchase_tax_ids = [line.tax_template_id.id for line in
                                   fc.purchase_tax_definition_line]

    type = fields.Selection([('view', u'Visão'),
                             ('normal', 'Normal'),
                             ('extension', u'Extensão')],
                            string='Tipo',
                            default='normal')

    note = fields.Text(u'Observações')

    inv_copy_note = fields.Boolean(
        u'Copiar Observação',
        help=u"Copia a observação no documento fiscal")

    parent_id = fields.Many2one(
        'account.product.fiscal.classification.template',
        string='Parent Fiscal Classification',
        domain="[('type', 'in', ('view', 'normal'))]",
        ondelete='cascade')

    child_ids = fields.One2many(
        'account.product.fiscal.classification.template',
        'parent_id', string='Child Fiscal Classifications')

    sale_tax_definition_line = fields.One2many(
        'l10n_br_tax.definition.sale.template',
        'fiscal_classification_id', 'Taxes Definitions')

    sale_tax_ids = fields.Many2many(
        'account.tax.template', string='Sale Taxes',
        compute='_compute_taxes')

    purchase_tax_definition_line = fields.One2many(
        'l10n_br_tax.definition.purchase.template',
        'fiscal_classification_id', 'Taxes Definitions')

    purchase_tax_ids = fields.Many2many(
        'account.tax.template', string='Purchase Taxes',
        compute='_compute_taxes')

    tax_estimate_ids = fields.One2many(
        comodel_name='l10n_br_tax.estimate.template',
        inverse_name='fiscal_classification_id',
        string=u'Impostos Estimados')

    _sql_constraints = [
        ('account_fiscal_classfication_code_uniq', 'unique (code)',
         u'Já existe um classificação fiscal com esse código!')]


class L10nBrTaxDefinitionTemplateModel(L10nBrTaxDefinitionTemplate):
    """Model for tax definition template"""

    fiscal_classification_id = fields.Many2one(
        'account.product.fiscal.classification.template',
        'Fiscal Classification', select=True)
    tax_ipi_guideline_id = fields.Many2one(
        'l10n_br_account_product.ipi_guideline', string=u'Enquadramento IPI')
    tax_icms_relief_id = fields.Many2one(
        'l10n_br_account_product.icms_relief', string=u'Desoneração ICMS')

    _sql_constraints = [
        ('l10n_br_tax_definition_template_tax_template_id_uniq', 'unique \
         (tax_template_id, fiscal_classification_id)',
         u'Imposto já existente nesta classificação fiscal!')
    ]


class L10nBrTaxDefinitionSaleTemplate(L10nBrTaxDefinitionTemplateModel,
                                      models.Model):
    """Definition a class model for sales tax and tax code template"""
    _name = 'l10n_br_tax.definition.sale.template'


class L10nBrTaxDefinitionPurchaseTemplate(L10nBrTaxDefinitionTemplateModel,
                                          models.Model):
    """Definition a class model for purchase tax and tax code template"""
    _name = 'l10n_br_tax.definition.purchase.template'


class L10nBrTaxEstimateModel(models.AbstractModel):
    _name = 'l10n_br_tax.estimate.model'
    _auto = False

    active = fields.Boolean('Ativo', default=True)

    state_id = fields.Many2one(
        'res.country.state', 'Estado', required=True)

    federal_taxes_national = fields.Float(
        'Impostos Federais Nacional', default=0.00,
        digits_compute=dp.get_precision('Account'))

    federal_taxes_import = fields.Float(
        'Impostos Federais Importado', default=0.00,
        digits_compute=dp.get_precision('Account'))

    state_taxes = fields.Float(
        'Impostos Estaduais Nacional', default=0.00,
        digits_compute=dp.get_precision('Account'))

    municipal_taxes = fields.Float(
        'Impostos Municipais Nacional', default=0.00,
        digits_compute=dp.get_precision('Account'))

    create_date = fields.Datetime(
        u'Data de Criação', readonly=True)

    key = fields.Char('Chave', size=32)

    version = fields.Char(u'Versão', size=32)

    origin = fields.Char('Fonte', size=32)

    company_id = fields.Many2one(
        comodel_name='res.company'
    )


class L10nBrTaxEstimateTemplate(models.Model):
    _name = 'l10n_br_tax.estimate.template'
    _inherit = 'l10n_br_tax.estimate.model'

    fiscal_classification_id = fields.Many2one(
        'account.product.fiscal.classification.template',
        'Fiscal Classification', select=True)
