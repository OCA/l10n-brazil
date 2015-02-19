# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
# Copyright (C) 2012  Raphaël Valyi - Akretion                                #
# Copyright (C) 2014  Luis Felipe Miléo - KMEE - www.kmee.com.br              #
# Copyright (C) 2015  Michell Stuttgart - KMEE                                #
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

from openerp import models, fields, api


class StockIncoterms(models.Model):
    _inherit = 'stock.incoterms'

    freight_responsibility = fields.Selection(
        selection=[('0', 'Emitente'),
                   ('1', u'Destinatário'),
                   ('2', 'Terceiros'),
                   ('9', 'Sem Frete')],
        string='Frete por Conta',
        required=True,
        default='0')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.one
    @api.model
    @api.returns
    def _default_fiscal_category(self):
        user_model = self.env['res.users']

        stock_fiscal_category = user_model.company_id.stock_fiscal_category_id
        stock_fiscal_category_id = \
            user_model.company_id.stock_fiscal_category_id.id

        return stock_fiscal_category and stock_fiscal_category_id or False

    fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string='Categoria Fiscal',
        readonly=True,
        domain="[('state', '=', 'approved')]",
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_category
    )

    fiscal_position = fields.Many2one(
        comodel_name='account.fiscal.position',
        string=u'Posição Fiscal',
        domain="[('fiscal_category_id','=',fiscal_category_id)]",
        readonly=True,
        states={'draft': [('readonly', False)]}
    )

    ind_pres = fields.Selection(
        selection=[('0', u'Não se aplica'),
                   ('1', u'Operação presencial'),
                   ('2', u'Operação não presencial, pela Internet'),
                   ('3', u'Operação não presencial, Teleatendimento'),
                   ('4', u'NFC-e em operação com entrega em domicílio'),
                   ('9', u'Operação não presencial, outros'),],
        string=u'Tipo de operação',
        default='0',
        help=u'Indicador de presença do comprador no estabelecimento '
             u'comercial no momento da operação.')

    @api.multi
    # @api.onchange('partner_id')
    def onchange_partner_id(self, partner_id, company_id, context=None):

        if context is None:
            context = {}

        result = super(StockPicking, self).onchange_partner_id(
            self._cr, self._uid, self._ids, partner_id=partner_id,
            company_id=company_id)

        if not partner_id or not company_id or 'fiscal_category_id' not in \
                context:
            return result

        result['value'].update(context['fiscal_category_id'])
        return result

    # @api.model
    # @api.onchange('fiscal_category_id')
    @api.multi
    def onchange_fiscal_category_id(self, partner_id, company_id=False,
                                    fiscal_category_id=False,
                                    context=None, **kwargs):

        if not context:
            context = {}

        result = {'value': {'fiscal_position': False}}

        if not partner_id or not company_id:
            return result

        partner = self.env['res.partner'].browse(partner_id)
        partner_address = partner.address_get(['invoice', 'delivery'])

        partner_invoice_id = partner_address['invoice']
        partner_shipping_id = partner_address['delivery']

        kwargs = {
            'partner_id': partner_id,
            'partner_invoice_id': partner_invoice_id,
            'partner_shipping_id': partner_shipping_id,
            'company_id': company_id,
            'context': context,
            'fiscal_category_id': fiscal_category_id
        }
        return self._fiscal_position_map(result, **kwargs)


    @api.model
    @api.onchange('company_id')
    def onchange_company_id(self):

        result = {'value': {'fiscal_position': False}}

        if not self.partner_id or not self.company_id:
            return result

        partner_invoice_id = self.env['res.partner'].address_get(
            [self.partner_id], ['invoice'])['invoice']
        partner_shipping_id = self.env['res.partner'].address_get(
            [self.partner_id], ['delivery'])['delivery']

        kwargs = {
            'partner_id': self.partner_id,
            'partner_invoice_id': partner_invoice_id,
            'partner_shipping_id': partner_shipping_id,
            'company_id': self.company_id,
            'context': self._context,
            'fiscal_category_id': self.fiscal_category_id
        }
        return self._fiscal_position_map(result, **kwargs)

    @api.model
    @api.returns
    def _prepare_invoice_line(self, group, picking, move_line,
                              invoice_id, invoice_vals):
        result = super(StockPicking, self)._prepare_invoice_line(
            group, picking, move_line, invoice_id, invoice_vals)

        fiscal_position = move_line.fiscal_position or \
            move_line.picking_id.fiscal_position or False
        fiscal_category_id = move_line.fiscal_category_id or \
            move_line.picking_id.fiscal_category_id or False
              
        result['cfop_id'] = fiscal_position and fiscal_position.cfop_id and \
                            fiscal_position.cfop_id.id
        result['fiscal_category_id'] = fiscal_category_id and \
                                       fiscal_category_id.id
        result['fiscal_position'] = fiscal_position and fiscal_position.id

        result['partner_id'] = picking.partner_id.id
        result['company_id'] = picking.company_id.id

        return result

    @api.model
    @api.returns
    def _prepare_invoice(self, picking, partner, inv_type, journal_id):
        result = super(StockPicking, self)._prepare_invoice(
            self._cr, self._uid, picking, partner, inv_type, journal_id,
            self._context)

        comment = ''
        if picking.fiscal_position.inv_copy_note:
            comment += picking.fiscal_position.note or ''

        if picking.note:
            comment += ' - ' + picking.note

        result['comment'] = comment
        result['fiscal_category_id'] = \
            picking.fiscal_category_id and picking.fiscal_category_id.id
        result['fiscal_position'] = \
            picking.fiscal_position and picking.fiscal_position.id
        result['ind_pres'] = picking.ind_pres
        return result


class StockMove(models.Model):

    _inherit = "stock.move"

    fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string='Categoria Fiscal',
        domain="[('type', '=', 'output'), ('journal_type', '=', 'sale')]",
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

    fiscal_position = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Fiscal Position',
        domain="[('fiscal_category_id','=',fiscal_category_id)]",
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

    @api.model
    @api.returns
    def _fiscal_position_map(self, result, **kwargs):
        kwargs['context'].update({'use_domain': ('use_picking', '=', True)})
        fp_rule_obj = self.env['account.fiscal.position.rule']
        return fp_rule_obj.apply_fiscal_mapping(result, **kwargs)

    # TODO: [new api] Depends of odoo/addons/stock.py
    def onchange_product_id(self, cr, uid, ids, product_id, location_id,
                            location_dest_id, partner_id, context=False, **kwargs):

        if not context:
            context = {}

        parent_fiscal_category_id = context.get('parent_fiscal_category_id')
        picking_type = context.get('picking_type')
        if context.get('company_id', False):
            company_id = context['company_id']
        else:
            company_id = self.pool.get('res.users').browse(
                cr, uid, uid, context=context).company_id.id

        result = {'value': {}}

        if parent_fiscal_category_id and product_id and picking_type:

            obj_fp_rule = self.pool.get('account.fiscal.position.rule')
            product_fc_id = obj_fp_rule.product_fiscal_category_map(
                cr, uid, product_id, parent_fiscal_category_id)

            if product_fc_id:
                parent_fiscal_category_id = product_fc_id

            result['value']['fiscal_category_id'] = parent_fiscal_category_id

            partner_invoice_id = self.pool.get('res.partner').address_get(
                cr, uid, [partner_id], ['invoice'])['invoice']
            partner_shipping_id = self.pool.get('res.partner').address_get(
                cr, uid, [partner_id], ['delivery'])['delivery']

            kwargs = {
                'partner_id': partner_id,
                'partner_invoice_id': partner_invoice_id,
                'partner_shipping_id': partner_shipping_id,
                'fiscal_category_id': parent_fiscal_category_id,
                'company_id': company_id,
                'context': context
            }

            result.update(self._fiscal_position_map(cr, uid, result, **kwargs))

        result_super = super(StockMove, self).onchange_product_id(
            cr, uid, ids, product_id, location_id, location_dest_id, partner_id)

        if 'value' in result_super:
            result_super['value'].update(result['value'])

        return result_super