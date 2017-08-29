# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

from .l10n_br_account import TYPE


class AccountFiscalPositionAbstract(object):

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        u'Categoria Fiscal'
    )

    type = fields.Selection(
        TYPE,
        related='fiscal_category_id.type',
        readonly=True,
        store=True,
        string=u'Fiscal Type'
    )

    inv_copy_note = fields.Boolean(
        string=u'Copiar Observação na Nota Fiscal'
    )

    asset_operation = fields.Boolean(
        string=u'Operação de Aquisição de Ativo',
        help=u"""Caso seja marcada essa opção, será incluido o IPI na base de
        calculo do ICMS."""
    )

    state = fields.Selection(
        [('draft', u'Rascunho'),
         ('review', u'Revisão'),
         ('approved', u'Aprovada'),
         ('unapproved', u'Não Aprovada')],
        string='Status',
        readonly=True,
        track_visibility='onchange',
        index=True,
        default='draft'
    )


class AccountFiscalPositionTaxAbstract(object):

    tax_group_id = fields.Many2one(
        comodel_name='account.tax.group',
        string=u'Grupo de Impostos',
    )

    @api.onchange('tax_src_id',
                  'tax_group_id',
                  'position_id')
    def onchange_tax_group(self):
        type_tax_use = {'input': 'purchase', 'output': 'sale'}

        domain = [('type_tax_use', 'in',
                   (type_tax_use.get(self.position_id.type), 'none'))]

        if self.tax_group_id:
            domain.append(('tax_group_id', '=', self.tax_group_id.id))

        if self.tax_src_id:
            domain.append(('tax_group_id', '=',
                           self.tax_src_id.tax_group_id.id))

        return {'domain': {'tax_dest_id': domain, 'tax_src_id': domain}}


class AccountFiscalPositionTemplate(AccountFiscalPositionAbstract,
                                    models.Model):
    _inherit = 'account.fiscal.position.template'

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
            tax_code_template = obj_tax_code_template.search(
                [('name', '=', tax_code.name)])
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
                'fiscal_category_id': (
                    position.fiscal_category_id and
                    position.fiscal_category_id.id or False
                )
            })
            for tax in position.tax_ids:
                obj_tax_fp.create({
                    'tax_src_id':
                    tax.tax_src_id and
                    tax_template_ref.get(tax.tax_src_id.id, False),
                    'tax_code_src_id':
                    tax.tax_code_src_id,
                    'type': position.type,
                    'state': position.state,
                    'type_tax_use': position.type_tax_use,
                    'cfop_id':
                    position.cfop_id and position.cfop_id.id or False,
                    'inv_copy_note': position.inv_copy_note,
                    'asset_operation': position.asset_operation,
                    'fiscal_category_id': (
                        position.fiscal_category_id and
                        position.fiscal_category_id.id or False
                    )
                })
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


class AccountFiscalPositionTaxTemplate(AccountFiscalPositionTaxAbstract,
                                       models.Model):

    _inherit = 'account.fiscal.position.tax.template'

    tax_src_id = fields.Many2one(
        comodel_name='account.tax.template',
        string='Tax on Product',
        required=False
    )


class AccountFiscalPosition(AccountFiscalPositionAbstract,
                            models.Model):

    _inherit = 'account.fiscal.position'

    @api.model
    def map_tax(self, taxes, product=None, partner=None):
        result = self.env['account.tax'].browse()

        if self.company_id and \
                self.env.context.get('type_tax_use') in ('sale', 'all'):
            if self.env.context.get('fiscal_type', 'product') == 'service':
                company_taxes = self.company_id.service_tax_ids

            if taxes:
                taxes |= company_taxes

        for tax in taxes:
            tax_count = 0
            for t in self.tax_ids:
                if (t.tax_src_id == tax or
                        t.tax_group_id == tax.tax_group_id):
                    tax_count += 1
                    if t.tax_dest_id:
                        result |= t.tax_dest_id
            if not tax_count:
                result |= tax
        return result


class AccountFiscalPositionTax(AccountFiscalPositionTaxAbstract,
                               models.Model):

    _inherit = 'account.fiscal.position.tax'

    tax_src_id = fields.Many2one(
        comodel_name='account.tax',
        string='Tax on Product',
        required=False
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
