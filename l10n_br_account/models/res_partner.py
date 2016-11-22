# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api

from .l10n_br_account import PRODUCT_FISCAL_TYPE, TYPE


class AccountFiscalPositionTemplate(models.Model):
    _inherit = 'account.fiscal.position.template'

    name = fields.Char('Fiscal Position', size=128, required=True)
    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal')
    fiscal_category_fiscal_type = fields.Selection(
        PRODUCT_FISCAL_TYPE, related='fiscal_category_id.fiscal_type',
        readonly=True, store=True, string='Fiscal Type')
    type = fields.Selection(
        TYPE, 'Tipo')
    type_tax_use = fields.Selection(
        [('sale', 'Sale'), ('purchase', 'Purchase'), ('all', 'All')],
        'Tax Application')
    inv_copy_note = fields.Boolean('Copiar Observação na Nota Fiscal')
    asset_operation = fields.Boolean(
        'Operação de Aquisição de Ativo',
        help="""Caso seja marcada essa opção, será incluido o IPI na base de
        calculo do ICMS.""")
    state = fields.Selection(
        [('draft', u'Rascunho'),
         ('review', u'Revisão'), ('approved', u'Aprovada'),
         ('unapproved', u'Não Aprovada')], 'Status', readonly=True,
        track_visibility='onchange', select=True, default='draft')

    @api.onchange('type')
    def onchange_type(self):
        type_tax = {'input': 'purhcase', 'output': 'sale'}
	self.type_tax_use = type_tax.get(self.type, 'none')
	self.tax_ids = False

    @api.onchange('fiscal_category_id')
    def onchange_fiscal_category_id(self):
        if self.fiscal_category_id:
            self.fiscal_category_fiscal_type = self.fiscal_category_id.fiscal_type

    def generate_fiscal_position(self, chart_temp_id,
                                 tax_template_ref, acc_template_ref,
                                 company_id):
        """
        This method generate Fiscal Position, Fiscal Position Accounts and
        Fiscal Position Taxes from templates.

        :param chart_temp_id: Chart Template Id.
        :param taxes_ids: Taxes templates reference for generating
        account.fiscal.position.tax.
        :param acc_template_ref: Account templates reference for generating
        account.fiscal.position.account.
        :param company_id: selected from wizard.multi.charts.accounts.
        :returns: True
        """
        obj_tax_fp = self.env['account.fiscal.position.tax']
        obj_ac_fp = self.env['account.fiscal.position.account']
        obj_fiscal_position = self.env['account.fiscal.position']
        obj_tax_code = self.env['account.tax.code']
        obj_tax_code_template = self.env['account.tax.code.template']
        tax_code_template_ref = {}
        tax_code_ids = obj_tax_code.search([('company_id', '=', company_id)])

        for tax_code in tax_code_ids:
            tax_code_template = obj_tax_code_template.search([('name', '=', tax_code.name)])
            if tax_code_template:
                tax_code_template_ref[tax_code_template[0].id] = tax_code.id

        fp_ids = self.search([('chart_template_id', '=', chart_temp_id)])
        for position in fp_ids:
            new_fp = obj_fiscal_position.create({
                'company_id': company_id,
                'name': position.name,
                'note': position.note,
                'type': position.type,
                'state': position.state,
                'type_tax_use': position.type_tax_use,
                'cfop_id':
                    position.cfop_id and position.cfop_id.id or False,
                'inv_copy_note': position.inv_copy_note,
                'asset_operation': position.asset_operation,
                'fiscal_category_id': position.fiscal_category_id and position.fiscal_category_id.id or False})
            for tax in position.tax_ids:
                obj_tax_fp.create({
                    'tax_src_id':
                    tax.tax_src_id and
                    tax_template_ref.get(tax.tax_src_id.id, False),
                    'tax_code_src_id':
                    tax.tax_code_src_id and
                    tax_code_template_ref.get(tax.tax_code_src_id.id, False),
                    'tax_src_domain': tax.tax_src_domain,
                    'tax_dest_id': tax.tax_dest_id and
                    tax_template_ref.get(tax.tax_dest_id.id, False),
                    'tax_code_dest_id': tax.tax_code_dest_id and
                    tax_code_template_ref.get(tax.tax_code_dest_id.id, False),
                    'position_id': new_fp
                })
            for acc in position.account_ids:
                obj_ac_fp.create({
                    'account_src_id': acc_template_ref[acc.account_src_id.id],
                    'account_dest_id':
                    acc_template_ref[acc.account_dest_id.id],
                    'position_id': new_fp
                })
        return True


class AccountFiscalPositionTaxTemplate(models.Model):
    _inherit = 'account.fiscal.position.tax.template'

    tax_src_id = fields.Many2one(
        'account.tax.template', string='Tax Source', required=False)
    #tax_code_src_id = fields.Many2one(
    #    'account.tax.code.template', string=u'Código Taxa Origem')
    #TODO MIG
    # tax_src_domain = fields.Char(
    #     related='tax_src_id.domain', string='Tax Domain')
    #tax_code_dest_id = fields.Many2one(
    #    'account.tax.code.template', string='Replacement Tax Code')

    @staticmethod
    def _tax_domain(tax_src_id, tax_code_src_id):
        tax_domain = False
        if tax_src_id:
            tax_domain = tax_src_id.domain
        if tax_code_src_id:
            tax_domain = tax_code_src_id.domain
        return tax_domain

    #@api.onchange('tax_src_id', 'tax_code_src_id')
    def onchange_tax_src_id(self):
        if self.tax_code_src_id or self.tax_src_id:
            self.tax_src_domain = self._tax_domain(
                self.tax_src_id,
                self.tax_code_src_id
            )


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    name = fields.Char('Fiscal Position', size=128, required=True)
    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal')
    fiscal_category_fiscal_type = fields.Selection(
        PRODUCT_FISCAL_TYPE, related='fiscal_category_id.fiscal_type',
        readonly=True, store=True, string='Fiscal Type')
    type = fields.Selection(
        TYPE, 'Tipo')
    type_tax_use = fields.Selection(
        [('sale', 'Sale'), ('purchase', 'Purchase'), ('all', 'All')],
        'Tax Application')
    inv_copy_note = fields.Boolean('Copiar Observação na Nota Fiscal')
    asset_operation = fields.Boolean(
        'Operação de Aquisição de Ativo',
        help="""Caso seja marcada essa opção, será incluido o IPI na base de
        calculo do ICMS.""")
    state = fields.Selection(
        [('draft', u'Rascunho'),
         ('review', u'Revisão'), ('approved', u'Aprovada'),
         ('unapproved', u'Não Aprovada')], 'Status', readonly=True,
        track_visibility='onchange', select=True, default='draft')

    @api.onchange('type')
    def onchange_type(self):
        type_tax = {'input': 'purhcase', 'output': 'sale'}
	self.type_tax_use = type_tax.get(self.type, 'none')
	self.tax_ids = False

    @api.onchange('fiscal_category_id')
    def onchange_fiscal_category_id(self):
        if self.fiscal_category_id:
            self.fiscal_category_fiscal_type = self.fiscal_category_id.fiscal_type


    #@TODO MIG

    # @api.v7
    # def map_tax(self, cr, uid, fposition_id, taxes, context=None):
    #     result = []
    #     if not context:
    #         context = {}
    #     if fposition_id and fposition_id.company_id and\
    #             context.get('type_tax_use') in ('sale', 'all'):
    #         if context.get('fiscal_type', 'product') == 'product':
    #             company_tax_ids = self.env['res.company').read(
    #                 cr, uid, fposition_id.company_id.id, ['product_tax_ids'],
    #                 context=context)['product_tax_ids']
    #         else:
    #             company_tax_ids = self.env['res.company').read(
    #                 cr, uid, fposition_id.company_id.id, ['service_tax_ids'],
    #                 context=context)['service_tax_ids']
    #
    #         company_taxes = self.env['account.tax').browse(
    #             cr, uid, company_tax_ids, context=context)
    #         if taxes:
    #             all_taxes = taxes + company_taxes
    #         else:
    #             all_taxes = company_taxes
    #         taxes = all_taxes
    #
    #     if not taxes:
    #         return []
    #     if not fposition_id:
    #         return map(lambda x: x.id, taxes)
    #     for t in taxes:
    #         ok = False
    #         tax_src = False
    #         for tax in fposition_id.tax_ids:
    #             tax_src = tax.tax_src_id and tax.tax_src_id.id == t.id
    #             tax_code_src = tax.tax_code_src_id and \
    #                 tax.tax_code_src_id.id == t.tax_code_id.id
    #
    #             if tax_src or tax_code_src:
    #                 if tax.tax_dest_id:
    #                     result.append(tax.tax_dest_id.id)
    #                 ok = True
    #         if not ok:
    #             result.append(t.id)
    #
    #     return list(set(result))
    #
    # @api.v8
    # def map_tax(self, taxes):
    #     result = self.env['account.tax'].browse()
    #     if self.company_id and \
    #             self.env.context.get('type_tax_use') in ('sale', 'all'):
    #         if self.env.context.get('fiscal_type', 'product') == 'product':
    #             company_taxes = self.company_id.product_tax_ids
    #         else:
    #             company_taxes = self.company_id.service_tax_ids
    #
    #         if taxes:
    #             taxes |= company_taxes
    #
    #     for tax in taxes:
    #         for t in self.tax_ids:
    #             if t.tax_src_id == tax or t.tax_code_src_id == tax.tax_code_id:
    #                 if t.tax_dest_id:
    #                     result |= t.tax_dest_id
    #                 break
    #         else:
    #             result |= tax
    #     return result


class AccountFiscalPositionTax(models.Model):
    _inherit = 'account.fiscal.position.tax'

    tax_src_id = fields.Many2one(
        'account.tax', string='Tax Source', required=False)
    # TODO MIG
    tax_code_src_id = fields.Many2one(
        'account.tax.group', u'Código Taxa Origem')
    #TODO MIG
    #tax_src_domain = fields.Char(related='tax_src_id.domain')
    tax_code_dest_id = fields.Many2one(
        'account.tax.group', 'Replacement Tax Code')

    @staticmethod
    def _tax_domain(tax_src_id, tax_code_src_id):
        tax_domain = False
        if tax_src_id:
            tax_domain = tax_src_id.domain
        if tax_code_src_id:
            tax_domain = tax_code_src_id.domain
        return tax_domain

    #@api.onchange('tax_src_id', 'tax_code_src_id')
    def onchange_tax_src_id(self):
        if self.tax_code_src_id or self.tax_src_id:
            self.tax_src_domain = self._tax_domain(
                self.tax_src_id,
                self.tax_code_src_id
            )


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _default_partner_fiscal_type_id(self, is_company=False):
        """Define o valor padão para o campo tipo fiscal, por padrão pega
        o tipo fiscal para não contribuinte já que quando é criado um novo
        parceiro o valor do campo is_company é false"""
        ft_ids = self.env['l10n_br_account.partner.fiscal.type'].search(
            [('default', '=', 'True'), ('is_company', '=', is_company)],
            limit=1)
        return ft_ids

    partner_fiscal_type_id = fields.Many2one(
        'l10n_br_account.partner.fiscal.type', 'Tipo Fiscal do Parceiro',
        domain="[('is_company', '=', is_company)]",
        default=_default_partner_fiscal_type_id)

    partner_special_fiscal_type_id = fields.Many2many(
        comodel_name='l10n_br_account.partner.special.fiscal.type',
        relation='res_partner_l10n_br_special_type',
        string='Regime especial'
    )

    @api.onchange('is_company')
    def _onchange_is_company(self):
        self.partner_fiscal_type_id = \
            self._default_partner_fiscal_type_id(self.is_company)
