# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion                                    #
# Copyright (C) 2012  Raphaël Valyi - Akretion
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU Affero General Public License as published by    #
#the Free Software Foundation, either version 3 of the License, or              #
#(at your option) any later version.                                            #
#                                                                               #
#This program is distributed in the hope that it will be useful,                #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                 #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                  #
#GNU Affero General Public License for more details.                            #
#                                                                               #
#You should have received a copy of the GNU Affero General Public License       #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

from osv import osv, fields


class stock_incoterms(osv.osv):
    _inherit = "stock.incoterms"

    _columns = {
                'freight_responsibility': fields.selection([('0', 'Emitente'), ('1', 'Destinatário'), ('2', 'Terceiros'), ('9', 'Sem Frete')], 'Frete por Conta', required=True),
                }

    _defaults = {
                 'freight_responsibility': 0,
                 }

stock_incoterms()


class stock_picking(osv.osv):
    _inherit = "stock.picking"

    _columns = {
                'fiscal_operation_category_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria'),
                'fiscal_operation_id': fields.many2one('l10n_br_account.fiscal.operation', 'Operação Fiscal',
                                                       domain="[('fiscal_operation_category_id','=',fiscal_operation_category_id)]"),
                'fiscal_position': fields.many2one('account.fiscal.position', 'Posição Fiscal',
                                                   domain="[('fiscal_operation_id','=',fiscal_operation_id)]"),
                }

    def _default_fiscal_operation_category(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.stock_fiscal_category_operation_id and user.company_id.stock_fiscal_category_operation_id.id

    _defaults = {
                'fiscal_operation_category_id': _default_fiscal_operation_category,
                }

    def _fiscal_position_map(self, cr, uid, partner_id, partner_invoice_id=False,
                             company_id=False, fiscal_operation_category_id=False):
        obj_fiscal_position_rule = self.pool.get('account.fiscal.position.rule')
        result = obj_fiscal_position_rule.fiscal_position_map(cr, uid, partner_id, partner_invoice_id,
                                                              company_id, fiscal_operation_category_id,
                                                              context={'use_domain': ('use_picking', '=', True)})
        return result

    def onchange_partner_in(self, cr, uid, context=None, partner_address_id=None,
                            company_id=False, fiscal_operation_category_id=False):
        result = super(stock_picking, self).onchange_partner_in(cr, uid, context, partner_address_id)
        if result and partner_address_id:
            partner_addr = self.pool.get('res.partner.address').browse(cr, uid, partner_address_id)
            partner_id = partner_addr.partner_id and partner_addr.partner_id.id
            fiscal_data = self._fiscal_position_map(cr, uid, partner_id, partner_address_id, company_id, fiscal_operation_category_id)
            result['value'].update(fiscal_data)
        return result

    def onchange_fiscal_operation_category_id(self, cr, uid, ids, partner_address_id,
                                              company_id=False, fiscal_operation_category_id=False):
        result = {'value': {}}
        if partner_address_id:
            partner_addr = self.pool.get('res.partner.address').browse(cr, uid, partner_address_id)
            partner_id = partner_addr.partner_id and partner_addr.partner_id.id
            fiscal_data = self._fiscal_position_map(cr, uid, partner_id, partner_address_id, company_id, fiscal_operation_category_id)
            result['value'].update(fiscal_data)
        return result

    def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id,
        invoice_vals, context=None):
        res = super(stock_picking, self)._prepare_invoice_line(cr, uid, group, picking, move_line, invoice_id, invoice_vals, context)
        if move_line.sale_line_id:
            fiscal_operation_id = move_line.sale_line_id.fiscal_operation_id or move_line.sale_line_id.order_id.fiscal_operation_id
            fiscal_operation_category_id = move_line.sale_line_id.fiscal_operation_category_id or move_line.sale_line_id.order_id.fiscal_operation_category_id
        elif move_line.purchase_line_id:
            fiscal_operation_id = move_line.purchase_line_id.fiscal_operation_id or move_line.purchase_line_id.order_id.fiscal_operation_id
            fiscal_operation_category_id = move_line.purchase_line_id.fiscal_operation_category_id or move_line.purchase_line_id.order_id.fiscal_operation_category_id
        else:
            fiscal_operation_id = move_line.picking_id.fiscal_operation_id
            fiscal_operation_category_id = move_line.picking_id.fiscal_operation_category_id
        res['cfop_id'] = fiscal_operation_id and fiscal_operation_id.cfop_id and fiscal_operation_id.cfop_id.id
        res['fiscal_operation_category_id'] = fiscal_operation_category_id and fiscal_operation_category_id.id
        res['fiscal_operation_id'] = fiscal_operation_id and fiscal_operation_id.id
        return res

    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        res = super(stock_picking, self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context)
        res['fiscal_operation_category_id'] = picking.fiscal_operation_category_id and picking.fiscal_operation_category_id.id
        res['fiscal_operation_id'] = picking.fiscal_operation_id and picking.fiscal_operation_id.id
        res['fiscal_document_id'] = picking.fiscal_operation_id and picking.fiscal_operation_id.fiscal_document_id and picking.fiscal_operation_id.fiscal_document_id.id
        res['fiscal_position'] = picking.fiscal_position and picking.fiscal_position.id
        res['document_serie_id'] = picking.company_id.document_serie_product_ids[0].id  # TODO pick 1st active one!!
        return res

stock_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
