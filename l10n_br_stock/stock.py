# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
# Copyright (C) 2012  Raphaël Valyi - Akretion                                #
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

from openerp.osv import orm, fields
from openerp.tools.translate import _


class stock_incoterms(orm.Model):
    _inherit = 'stock.incoterms'
    _columns = {
        'freight_responsibility': fields.selection(
            [('0', 'Emitente'),
            ('1', u'Destinatário'),
            ('2', 'Terceiros'),
            ('9', 'Sem Frete')],
            'Frete por Conta', required=True)
    }
    _defaults = {
        'freight_responsibility': 0
    }


class stock_picking(orm.Model):
    _inherit = 'stock.picking'

    def _default_fiscal_category(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(
            cr, uid, uid, context=context)
        return user.company_id.stock_fiscal_category_id and \
        user.company_id.stock_fiscal_category_id.id or False

    _columns = {
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria Fiscal',
            readonly=True, states={'draft': [('readonly', False)]}),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', u'Posição Fiscal',
            domain="[('fiscal_category_id','=',fiscal_category_id)]",
            readonly=True, states={'draft': [('readonly', False)]})
    }
    _defaults = {
        'fiscal_category_id': _default_fiscal_category
    }

    def onchange_partner_in(self, cr, uid, ids, partner_id=None,
                            company_id=None, context=None,
                            fiscal_category_id=None):
        if not context:
            context = {}

        return super(stock_picking, self).onchange_partner_in(
            cr, uid, ids, partner_id=partner_id, company_id=company_id,
            context=context, fiscal_category_id=fiscal_category_id)

    def onchange_fiscal_category_id(self, cr, uid, ids,
                                    partner_id, company_id=False,
                                    fiscal_category_id=False,
                                    context=None, **kwargs):
        if not context:
            context = {}

        result = {'value': {'fiscal_position': False}}

        if not partner_id or not company_id:
            return result

        partner_invoice_id = self.pool.get('res.partner').address_get(
            cr, uid, [partner_id], ['invoice'])['invoice']
        partner_shipping_id = self.pool.get('res.partner').address_get(
            cr, uid, [partner_id], ['delivery'])['delivery']

        kwargs = {
           'partner_id': partner_id,
           'partner_invoice_id': partner_invoice_id,
           'partner_shipping_id': partner_shipping_id,
           'company_id': company_id,
           'context': context,
           'fiscal_category_id': fiscal_category_id
        }
        return self._fiscal_position_map(cr, uid, result, **kwargs)

    def onchange_company_id(self, cr, uid, ids, partner_id, company_id=False,
                            fiscal_category_id=False, context=None, **kwargs):
        if not context:
            context = {}

        result = {'value': {'fiscal_position': False}}

        if not partner_id or not company_id:
            return result

        partner_invoice_id = self.pool.get('res.partner').address_get(
            cr, uid, [partner_id], ['invoice'])['invoice']
        partner_shipping_id = self.pool.get('res.partner').address_get(
            cr, uid, [partner_id], ['delivery'])['delivery']

        kwargs = {
           'partner_id': partner_id,
           'partner_invoice_id': partner_invoice_id,
           'partner_shipping_id': partner_shipping_id,
           'company_id': company_id,
           'context': context,
           'fiscal_category_id': fiscal_category_id
        }
        return self._fiscal_position_map(cr, uid, result, **kwargs)

    def _prepare_invoice_line(self, cr, uid, group, picking, move_line,
                              invoice_id, invoice_vals, context=None):
        result = super(stock_picking, self)._prepare_invoice_line(
            cr, uid, group, picking, move_line, invoice_id, invoice_vals,
            context)

        fiscal_position = move_line.picking_id.fiscal_position
        fiscal_category_id = move_line.picking_id.fiscal_category_id

        result['cfop_id'] = fiscal_position and \
        fiscal_position.cfop_id and fiscal_position.cfop_id.id
        result['fiscal_category_id'] = fiscal_category_id and \
        fiscal_category_id.id
        result['fiscal_position'] = fiscal_position and \
        fiscal_position.id

        result['partner_id'] = picking.partner_id.id
        result['company_id'] = picking.company_id.id

        return result

    def _prepare_invoice(self, cr, uid, picking, partner,
                        inv_type, journal_id, context=None):
        result = super(stock_picking, self)._prepare_invoice(
            cr, uid, picking, partner, inv_type, journal_id, context)

        comment = ''
        if picking.fiscal_position.inv_copy_note:
            comment += picking.fiscal_position.note or ''

        if picking.note:
            comment += ' - ' + picking.note

        result['comment'] = comment
        result['fiscal_category_id'] = picking.fiscal_category_id and \
        picking.fiscal_category_id.id
        result['fiscal_position'] = picking.fiscal_position and \
        picking.fiscal_position.id
        return result


class stock_picking_in(stock_picking):
    _inherit = 'stock.picking.in'

    def _default_fiscal_category(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(
            cr, uid, uid, context=context)
        return user.company_id.stock_in_fiscal_category_id and \
        user.company_id.stock_in_fiscal_category_id.id or False

    _columns = {
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria Fiscal',
            domain="[('journal_type', 'in', ('sale_refund', 'purchase')), "
            "('fiscal_type', '=', 'product'), ('type', '=', 'input')]"),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', u'Posição Fiscal',
            domain="[('fiscal_category_id','=',fiscal_category_id)]")
    }
    _defaults = {
        'invoice_state': 'none',
        'fiscal_category_id': _default_fiscal_category
    }

    def _fiscal_position_map(self, cr, uid, result, **kwargs):
        kwargs['context'].update({'use_domain': ('use_picking', '=', True)})
        fp_rule_obj = self.pool.get('account.fiscal.position.rule')
        return fp_rule_obj.apply_fiscal_mapping(cr, uid, result, kwargs)

    def onchange_partner_in(self, cr, uid, ids, partner_id=None,
                            company_id=None, context=None,
                            fiscal_category_id=None):

        result = super(stock_picking, self).onchange_partner_in(
            cr, uid, partner_id, context)

        if not result:
            result = {'value': {'fiscal_position': False}}

        if not partner_id or not company_id:
            return result

        partner_invoice_id = self.pool.get('res.partner').address_get(
            cr, uid, [partner_id], ['invoice'])['invoice']
        partner_shipping_id = self.pool.get('res.partner').address_get(
            cr, uid, [partner_id], ['delivery'])['delivery']

        kwargs = {
           'partner_id': partner_id,
           'partner_invoice_id': partner_invoice_id,
           'partner_shipping_id': partner_shipping_id,
           'company_id': company_id,
           'fiscal_category_id': fiscal_category_id,
           'context': context
        }
        return self._fiscal_position_map(cr, uid, result, **kwargs)


class stock_picking_out(stock_picking):
    _inherit = 'stock.picking.out'

    def _default_fiscal_category(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(
            cr, uid, uid, context=context)
        return user.company_id.stock_out_fiscal_category_id and \
        user.company_id.stock_out_fiscal_category_id.id or False

    _columns = {
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria Fiscal',
            domain="[('journal_type', 'in', ('purchase_refund', 'sale')), "
            "('fiscal_type', '=', 'product'), ('type', '=', 'output')]"),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', u'Posição Fiscal',
            domain="[('fiscal_category_id','=',fiscal_category_id)]")
    }
    _defaults = {
        'invoice_state': 'none',
        'fiscal_category_id': _default_fiscal_category,
    }

    def _fiscal_position_map(self, cr, uid, result, **kwargs):
        kwargs['context'].update({'use_domain': ('use_picking', '=', True)})
        fp_rule_obj = self.pool.get('account.fiscal.position.rule')
        return fp_rule_obj.apply_fiscal_mapping(cr, uid, result, kwargs)

    def onchange_partner_in(self, cr, uid, ids, partner_id=None,
                            company_id=None, context=None,
                            fiscal_category_id=None):

        result = super(stock_picking, self).onchange_partner_in(
            cr, uid, partner_id, context)

        if not result:
            result = {'value': {'fiscal_position': False}}

        if not partner_id or not company_id:
            return result

        partner_invoice_id = self.pool.get('res.partner').address_get(
            cr, uid, [partner_id], ['invoice'])['invoice']
        partner_shipping_id = self.pool.get('res.partner').address_get(
            cr, uid, [partner_id], ['delivery'])['delivery']

        kwargs = {
           'partner_id': partner_id,
           'partner_invoice_id': partner_invoice_id,
           'partner_shipping_id': partner_shipping_id,
           'company_id': company_id,
           'fiscal_category_id': fiscal_category_id,
           'context': context
        }
        return self._fiscal_position_map(cr, uid, result, **kwargs)
