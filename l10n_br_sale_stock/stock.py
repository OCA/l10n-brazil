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

from openerp.osv import orm


class StockPicking(orm.Model):
    _inherit = 'stock.picking'

    def _prepare_invoice(self, cr, uid, picking, partner,
                        inv_type, journal_id, context=None):
        result = super(StockPicking, self)._prepare_invoice(
            cr, uid, picking, partner, inv_type, journal_id, context)

        fp_comment = []
        fc_comment = []
        fp_ids = []
        fc_ids = []

        if picking.fiscal_position and \
        picking.fiscal_position.inv_copy_note and \
        picking.fiscal_position.note:
            fp_comment.append(picking.fiscal_position.note)

        for move in picking.move_lines:
            if move.sale_line_id:
                line = move.sale_line_id
                if line.fiscal_position and \
                line.fiscal_position.inv_copy_note and \
                line.fiscal_position.note:
                    if not line.fiscal_position.id in fp_ids:
                        fp_comment.append(line.fiscal_position.note)
                        fp_ids.append(line.fiscal_position.id)

            if move.product_id.ncm_id:
                fc = move.product_id.ncm_id
                if fc.inv_copy_note and fc.note:
                    if not fc.id in fc_ids:
                        fc_comment.append(fc.note)
                        fc_ids.append(fc.id)

        result['comment'] = " - ".join(fp_comment + fc_comment)
        result['fiscal_category_id'] = picking.fiscal_category_id and \
        picking.fiscal_category_id.id
        result['fiscal_position'] = picking.fiscal_position and \
        picking.fiscal_position.id
        return result
