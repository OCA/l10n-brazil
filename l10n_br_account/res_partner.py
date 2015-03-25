# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel               #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

from openerp import api, models, fields


class AccountFiscalPositionTemplate(models.Model):
    _inherit = 'account.fiscal.position.template'

    name = fields.Char(string='Fiscal Position', size=128, required=True)
    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', string='Categoria Fiscal')
    fiscal_category_fiscal_type = fields.Selection(
        related='fiscal_category_id.fiscal_type', readonly=True,
        store=True,
        string='Fiscal Type')
    type = fields.Selection([('input', 'Entrada'), ('output', 'Saida')],
                             string='Tipo')
    type_tax_use = fields.Selection(
        [('sale', 'Sale'), ('purchase', 'Purchase'), ('all', 'All')],
        string='Tax Application')
    inv_copy_note = fields.Boolean(string=u'Copiar Observação na Nota Fiscal')
    asset_operation = fields.Boolean(string=u'Operação de Aquisição de Ativo',
        help=u"""Caso seja marcada essa opção, será incluido o IPI na base de
            calculo do ICMS.""")
    id_dest = fields.Selection([('1', u'Operação interna'),
                                ('2', u'Operação interestadual'),
                                ('3', u'Operação com exterior')],
                               string=u'Local de destino da operação',
                               help=u'Identificador de local de destino da operação.')
    state = fields.Selection([('draft', u'Rascunho'),
                              ('review', u'Revisão'), ('approved', u'Aprovada'),
                              ('unapproved', u'Não Aprovada')], string='Status', readonly=True,
                             track_visibility='onchange', select=True, default='draft')

    def onchange_type(self, cr, uid, ids, type=False, context=None):
        type_tax = {'input': 'purchase', 'output': 'sale'}
        return {'value': {'type_tax_use': type_tax.get(type, 'all'),
                          'tax_ids': False}}

    def onchange_fiscal_category_id(self, cr, uid, ids,
                                    fiscal_category_id=False, context=None):
        if fiscal_category_id:
            fc_fields = self.pool.get('l10n_br_account.fiscal.category').read(
                    cr, uid, fiscal_category_id,
                    ['fiscal_type', 'journal_type'], context=context)
            return {'value': {'fiscal_category_fiscal_type': fc_fields['fiscal_type']}}

    def generate_fiscal_position(self, cr, uid, chart_temp_id,
                                 tax_template_ref, acc_template_ref,
                                 company_id, context=None):
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
        if context is None:
            context = {}

        obj_tax_fp = self.pool.get('account.fiscal.position.tax')
        obj_ac_fp = self.pool.get('account.fiscal.position.account')
        obj_fiscal_position = self.pool.get('account.fiscal.position')
        obj_tax_code = self.pool.get('account.tax.code')
        obj_tax_code_template = self.pool.get('account.tax.code.template')
        tax_code_template_ref = {}
        tax_code_ids = obj_tax_code.search(
            cr, uid, [('company_id', '=', company_id)])

        for tax_code in obj_tax_code.browse(cr, uid, tax_code_ids):
            tax_code_template = obj_tax_code_template.search(
                cr, uid, [('name', '=', tax_code.name)])
            if tax_code_template:
                tax_code_template_ref[tax_code_template[0]] = tax_code.id

        fp_ids = self.search(cr, uid,
            [('chart_template_id', '=', chart_temp_id)])
        for position in self.browse(cr, uid, fp_ids, context=context):
            new_fp = obj_fiscal_position.create(cr, uid,
                {'company_id': company_id,
                    'name': position.name,
                    'note': position.note,
                    'type': position.type,
                    'state': position.state,
                    'type_tax_use': position.type_tax_use,
                    'cfop_id': position.cfop_id and position.cfop_id.id or False,
                    'inv_copy_note': position.inv_copy_note,
                    'asset_operation': position.asset_operation,
                    'id_dest': position.id_dest,
                    'fiscal_category_id': position.fiscal_category_id and position.fiscal_category_id.id or False})
            for tax in position.tax_ids:
                obj_tax_fp.create(cr, uid, {
                    'tax_src_id': tax.tax_src_id and tax_template_ref.get(tax.tax_src_id.id, False),
                    'tax_code_src_id': tax.tax_code_src_id and tax_code_template_ref.get(tax.tax_code_src_id.id, False),
                    'tax_src_domain': tax.tax_src_domain,
                    'tax_dest_id': tax.tax_dest_id and tax_template_ref.get(tax.tax_dest_id.id, False),
                    'tax_code_dest_id': tax.tax_code_dest_id and tax_code_template_ref.get(tax.tax_code_dest_id.id, False),
                    'position_id': new_fp
                })
            for acc in position.account_ids:
                obj_ac_fp.create(cr, uid, {
                    'account_src_id': acc_template_ref[acc.account_src_id.id],
                    'account_dest_id': acc_template_ref[acc.account_dest_id.id],
                    'position_id': new_fp
                })
        return True


class AccountFiscalPositionTaxTemplate(models.Model):
    _inherit = 'account.fiscal.position.tax.template'

    tax_src_id = fields.Many2one('account.tax.template', string='Tax Source')
    tax_code_src_id = fields.Many2one('account.tax.code.template',
                                        string=u'Código Taxa Origem')
    tax_src_domain = fields.Char(related='tax_src_id.domain')
    tax_code_dest_id = fields.Many2one('account.tax.code.template',
                                        string='Replacement Tax Code')

    def _tax_domain(self, cr, uid, ids, tax_src_id=False,
                    tax_code_src_id=False, context=None):

        tax_domain = False
        if tax_src_id:
            tax_domain = self.pool.get('account.tax.template').read(
                cr, uid, tax_src_id, ['domain'], context=context)['domain']

        if tax_code_src_id:
            tax_domain = self.pool.get('account.tax.code.template').read(
                cr, uid, tax_code_src_id, ['domain'],
                context=context)['domain']

        return {'value': {'tax_src_domain': tax_domain}}

    def onchange_tax_src_id(self, cr, uid, ids, tax_src_id=False,
                            tax_code_src_id=False, context=None):

        return self._tax_domain(cr, uid, ids, tax_src_id, tax_code_src_id,
                                context=context)

    def onchange_tax_code_src_id(self, cr, uid, ids, tax_src_id=False,
                                 tax_code_src_id=False, context=None):

        return self._tax_domain(cr, uid, ids, tax_src_id, tax_code_src_id,
                                context=context)


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    name = fields.Char(string='Fiscal Position', size=128, required=True)
    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', string='Categoria Fiscal')
    fiscal_category_fiscal_type = fields.Selection(
        related='fiscal_category_id.fiscal_type', readonly=True,
        store=True,
        string='Fiscal Type')
    type = fields.Selection([('input', 'Entrada'), ('output', 'Saida')],
                             string='Tipo')
    type_tax_use = fields.Selection(
        [('sale', 'Sale'), ('purchase', 'Purchase'), ('all', 'All')],
        string='Tax Application')
    inv_copy_note = fields.Boolean(string=u'Copiar Observação na Nota Fiscal')
    asset_operation = fields.Boolean(string=u'Operação de Aquisição de Ativo',
        help=u"""Caso seja marcada essa opção, será incluido o IPI na base de
            calculo do ICMS.""")
    id_dest = fields.Selection([('1', u'Operação interna'),
                                ('2', u'Operação interestadual'),
                                ('3', u'Operação com exterior')],
                               string=u'Local de destino da operação',
                               help=u'Identificador de local de destino da operação.')
    state = fields.Selection([('draft', u'Rascunho'),
                              ('review', u'Revisão'), ('approved', u'Aprovada'),
                              ('unapproved', u'Não Aprovada')], string='Status', readonly=True,
                             track_visibility='onchange', select=True, default='draft')

    def onchange_type(self, cr, uid, ids, type=False, context=None):
        type_tax = {'input': 'purchase', 'output': 'sale'}
        return {'value': {'type_tax_use': type_tax.get(type, 'all'),
                          'tax_ids': False}}

    def onchange_fiscal_category_id(self, cr, uid, ids,
                                    fiscal_category_id=False, context=None):
        if fiscal_category_id:
            fc_fields = self.pool.get('l10n_br_account.fiscal.category').read(
                cr, uid, fiscal_category_id, ['fiscal_type', 'journal_type'],
                context=context)
            return {'value': {'fiscal_category_fiscal_type': fc_fields['fiscal_type']}}

    #TODO - Refatorar para trocar os impostos
    def map_tax_code(self, cr, uid, product_id, fiscal_position,
                     company_id=False, tax_ids=False, context=None):

        if not context:
            context = {}

        result = {}
        if tax_ids:

            product = self.pool.get('product.product').browse(
                cr, uid, product_id, context=context)

            fclassificaion = product.ncm_id

            if context.get('type_tax_use') == 'sale':

                if fclassificaion:
                    tax_sale_ids = fclassificaion.sale_tax_definition_line
                    for tax_def in tax_sale_ids:
                        if tax_def.tax_id.id in tax_ids and tax_def.tax_code_id:
                            result.update({tax_def.tax_id.domain:
                                           tax_def.tax_code_id.id})

                if company_id:
                    company = self.pool.get('res.company').browse(
                        cr, uid, company_id, context=context)

                    if context.get('fiscal_type', 'product') == 'product':
                        company_tax_def = company.product_tax_definition_line
                    else:
                        company_tax_def = company.service_tax_definition_line

                    for tax_def in company_tax_def:
                        if tax_def.tax_id.id in tax_ids and tax_def.tax_code_id:
                                result.update({tax_def.tax_id.domain:
                                               tax_def.tax_code_id.id})

            if context.get('type_tax_use') == 'purchase':

                if fclassificaion:
                    tax_purchase_ids = fclassificaion.purchase_tax_definition_line
                    for tax_def in tax_purchase_ids:
                        if tax_def.tax_id.id in tax_ids and tax_def.tax_code_id:
                            result.update({tax_def.tax_id.domain:
                                           tax_def.tax_code_id.id})

            if fiscal_position:
                for fp_tax in fiscal_position.tax_ids:
                    if fp_tax.tax_dest_id:
                        if fp_tax.tax_dest_id.id in tax_ids and fp_tax.tax_code_dest_id:
                            result.update({fp_tax.tax_dest_id.domain:
                                           fp_tax.tax_code_dest_id.id})
                    if not fp_tax.tax_dest_id and fp_tax.tax_code_src_id and \
                    fp_tax.tax_code_dest_id:
                        result.update({fp_tax.tax_code_src_id.domain:
                                       fp_tax.tax_code_dest_id.id})

        return result

    @api.v7
    def map_tax(self, cr, uid, fposition_id, taxes, context=None):
        result = []
        if not context:
            context = {}
        if fposition_id and fposition_id.company_id and \
                fposition_id.type_tax_use in ('sale', 'all'):
            
            if context.get('fiscal_type', 'product') == 'product':
                company_tax_ids = self.pool.get('res.company').read(
                    cr, uid, fposition_id.company_id.id, ['product_tax_ids'],
                    context=context)['product_tax_ids']
            else:
                company_tax_ids = self.pool.get('res.company').read(
                    cr, uid, fposition_id.company_id.id, ['service_tax_ids'],
                    context=context)['service_tax_ids']

            company_taxes = self.pool.get('account.tax').browse(
                    cr, uid, company_tax_ids, context=context)
            if taxes:
                all_taxes = taxes + company_taxes
            else:
                all_taxes = company_taxes
            taxes = all_taxes

        if not taxes:
            return []
        if not fposition_id:
            return map(lambda x: x.id, taxes)
        for t in taxes:
            ok = False
            tax_src = False
            for tax in fposition_id.tax_ids:
                tax_src = tax.tax_src_id and tax.tax_src_id.id == t.id
                tax_code_src = tax.tax_code_src_id and \
                    tax.tax_code_src_id.id == t.tax_code_id.id

                if tax_src or tax_code_src:
                    if tax.tax_dest_id:
                        result.append(tax.tax_dest_id.id)
                    ok = True
            if not ok:
                result.append(t.id)

        return list(set(result))

    @api.v8
    def map_tax(self, taxes):
        result = self._model.map_tax(self._cr, self._uid, self, taxes, self._context)
        result = self.env['account.tax'].browse(result)
        return result


class AccountFiscalPositionTax(models.Model):
    _inherit = 'account.fiscal.position.tax'

    tax_src_id = fields.Many2one('account.tax', string='Tax Source')
    tax_code_src_id = fields.Many2one(
        'account.tax.code', string=u'Código Taxa Origem')
    tax_src_domain = fields.Char(related='tax_src_id.domain')
    tax_code_dest_id = fields.Many2one(
        'account.tax.code', string='Replacement Tax Code')

    def _tax_domain(self, cr, uid, ids, tax_src_id=False,
                    tax_code_src_id=False, context=None):

        tax_domain = False
        if tax_src_id:
            tax_domain = self.pool.get('account.tax').read(
                cr, uid, tax_src_id, ['domain'], context=context)['domain']

        if tax_code_src_id:
            tax_domain = self.pool.get('account.tax.code').read(
                cr, uid, tax_code_src_id, ['domain'],
                context=context)['domain']

        return {'value': {'tax_src_domain': tax_domain}}

    def onchange_tax_src_id(self, cr, uid, ids, tax_src_id=False,
                            tax_code_src_id=False, context=None):

        return self._tax_domain(cr, uid, ids, tax_src_id, tax_code_src_id,
                                context=context)

    def onchange_tax_code_src_id(self, cr, uid, ids, tax_src_id=False,
                                 tax_code_src_id=False, context=None):

        return self._tax_domain(cr, uid, ids, tax_src_id, tax_code_src_id,
                                context=context)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _default_partner_fiscal_type_id(self):
        """Define o valor padão para o campo tipo fiscal, por padrão pega
        o tipo fiscal para não contribuinte já que quando é criado um novo
        parceiro o valor do campo is_company é false"""
        return self.env['l10n_br_account.partner.fiscal.type'].search(
            [('default', '=', 'True')], limit=1)

    partner_fiscal_type_id = fields.Many2one(
        'l10n_br_account.partner.fiscal.type', string='Tipo Fiscal do Parceiro',
        domain="[('is_company', '=', is_company)]",
        default=_default_partner_fiscal_type_id)

    def onchange_mask_cnpj_cpf(self, cr, uid, ids, is_company,
                            cnpj_cpf, context=None):
        result = super(ResPartner, self).onchange_mask_cnpj_cpf(
            cr, uid, ids, is_company, cnpj_cpf, context)
        ft_id = self._default_partner_fiscal_type_id(
            cr, uid, is_company, context)

        if ft_id:
            result['value']['partner_fiscal_type_id'] = ft_id
        return result
