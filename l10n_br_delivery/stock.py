# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
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


class StockPicking(orm.Model):
    _inherit = 'stock.picking'
    _columns = {
        'vehicle_id': fields.many2one(
            'l10n_br_delivery.carrier.vehicle', u'Veículo'),
        'incoterm': fields.many2one(
            'stock.incoterms', 'Tipo do Frete',
        help="Incoterm which stands for 'International Commercial terms"
        "implies its a series of sales terms which are used in the "
        "commercial transaction.")}

    def _prepare_shipping_invoice_line(self, cr, uid, picking,
                                    invoice, context=None):
        #TODO: Calcular o valor correto em caso de alteração da quantidade
        return False

    def _prepare_invoice_line(self, cr, uid, group, picking, move_line,
                              invoice_id, invoice_vals, context=None):
        result = super(StockPicking, self)._prepare_invoice_line(
            cr, uid, group, picking, move_line, invoice_id, invoice_vals,
            context)
        #TODO: Calcular o valor correto em caso de alteração da quantidade
        if move_line.sale_line_id:
            result['insurance_value'] = move_line.sale_line_id.insurance_value
            result['other_costs_value'] = move_line.sale_line_id.other_costs_value
            result['freight_value'] = move_line.sale_line_id.freight_value
        return result
