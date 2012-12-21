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

from osv import osv, fields


class stock_incoterms(osv.osv):
    _inherit = 'stock.incoterms'
    _columns = {
        'freight_responsibility': fields.selection([('0', 'Emitente'),
                                                    ('1', 'Destinatário'),
                                                    ('2', 'Terceiros'),
                                                    ('9', 'Sem Frete')], 
                                                   'Frete por Conta',
                                                   required=True)}

    _defaults = {
        'freight_responsibility': 0}

stock_incoterms()


class stock_picking(osv.osv):
    _inherit = "stock.picking"
    
    def _default_fiscal_category(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id.stock_fiscal_category_id and user.company_id.stock_fiscal_category_id.id
    
    _columns = {
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria'),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', 'Posição Fiscal',
            domain="[('fiscal_category_id','=',fiscal_category_id)]")}
    
    _defaults = {
         'fiscal_category_id': _default_fiscal_category}

    def _fiscal_position_map(self, cr, uid, partner_id,
                             partner_invoice_id=False, company_id=False,
                             fiscal_category_id=False):
        obj_fp_rule = self.pool.get('account.fiscal.position.rule')
        result = obj_fp_rule.fiscal_position_map(
            cr, uid, partner_id, partner_invoice_id, company_id,
            fiscal_category_id,
            context={'use_domain': ('use_picking', '=', True)})
        return result

    def onchange_partner_in(self, cr, uid, context=None,
                            partner_address_id=None, company_id=False,
                            fiscal_category_id=False):
        result = super(stock_picking, self).onchange_partner_in(
            cr, uid, context, partner_address_id)
        if result and partner_address_id:
            partner_addr = self.pool.get('res.partner.address').browse(
                cr, uid, partner_address_id)
            partner_id = partner_addr.partner_id and partner_addr.partner_id.id
            fiscal_data = self._fiscal_position_map(
                cr, uid, partner_id, partner_address_id, company_id,
                fiscal_category_id)
            result['value'].update(fiscal_data)
        return result

    def onchange_fiscal_category_id(self, cr, uid, ids, partner_address_id,
                                    company_id=False,
                                    fiscal_category_id=False):
        result = {'value': {}}
        if partner_address_id:
            partner_addr = self.pool.get('res.partner.address').browse(
                cr, uid, partner_address_id)
            partner_id = partner_addr.partner_id and partner_addr.partner_id.id
            fiscal_data = self._fiscal_position_map(
                cr, uid, partner_id, partner_address_id, company_id,
                fiscal_category_id)
            result['value'].update(fiscal_data)
        return result

    def _prepare_invoice_line(self, cr, uid, group, picking, move_line,
                              invoice_id, invoice_vals, context=None):
        result = super(stock_picking, self)._prepare_invoice_line(
            cr, uid, group, picking, move_line, invoice_id, invoice_vals,
            context)
        if move_line.sale_line_id:
            fiscal_position = move_line.sale_line_id.fiscal_position or move_line.sale_line_id.order_id.fiscal_position
            fiscal_category_id = move_line.sale_line_id.fiscal_category_id or move_line.sale_line_id.order_id.fiscal_category_id
            refund_fiscal_position = fiscal_category_id.refund_fiscal_category_id or False
        elif move_line.purchase_line_id:
            fiscal_position = move_line.purchase_line_id.fiscal_position or move_line.purchase_line_id.order_id.fiscal_position
            fiscal_category_id = move_line.purchase_line_id.fiscal_category_id or move_line.purchase_line_id.order_id.fiscal_category_id
            refund_fiscal_position = fiscal_category_id.refund_fiscal_category_id or False
        else:
            fiscal_position = move_line.picking_id.fiscal_position
            fiscal_category_id = move_line.picking_id.fiscal_category_id

        if context.get('inv_type') in ('in_refund', 'out_refund'):
            if not refund_fiscal_position:
                raise osv.except_osv(
                    _('Error!'),
                    _("This Fiscal Operation does not has Fiscal Operation \
                    for Returns!"))

            fiscal_category_id = refund_fiscal_position
            fiscal_data = self._fiscal_position_map(
                cr, uid, move_line.picking_id.partner_id.id,
                move_line.picking_id.address_id.id,
                move_line.picking_id.company_id.id,
                fiscal_category_id.id)

            fiscal_position = self.pool.get('account.fiscal.position').browse(
                cr, uid, fiscal_data.get('fiscal_position', 0))

        result['cfop_id'] = fiscal_position and fiscal_position.cfop_id and fiscal_position.cfop_id.id
        result['fiscal_category_id'] = fiscal_category_id and fiscal_category_id.id
        result['fiscal_position'] = fiscal_position and fiscal_position.id
        return result

    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        result = super(stock_picking, self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context)
        result['fiscal_category_id'] = picking.fiscal_category_id and picking.fiscal_category_id.id
        result['fiscal_position'] = picking.fiscal_position and picking.fiscal_position.id
        return result

stock_picking()
