# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
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


class stock_picking(orm.Model):
    _inherit = 'stock.picking'

    def _prepare_invoice_line(self, cr, uid, group, picking, move_line,
                              invoice_id, invoice_vals, context=None):
        result = super(stock_picking, self)._prepare_invoice_line(
            cr, uid, group, picking, move_line, invoice_id, invoice_vals,
            context)
        if move_line.purchase_line_id:
            fiscal_position = move_line.purchase_line_id.fiscal_position or \
            move_line.purchase_line_id.order_id.fiscal_position
            fiscal_category_id = move_line.purchase_line_id.fiscal_category_id or move_line.purchase_line_id.order_id.fiscal_category_id
        else:
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
