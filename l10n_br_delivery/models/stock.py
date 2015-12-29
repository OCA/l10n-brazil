# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    vehicle_id = fields.Many2one(
        'l10n_br_delivery.carrier.vehicle', u'Veículo')
    incoterm = fields.Many2one(
        'stock.incoterms', 'Tipo do Frete',
        help="Incoterm which stands for 'International Commercial terms"
        "implies its a series of sales terms which are used in the "
        "commercial transaction.")

    # TODO migrate to new API
    def _prepare_shipping_invoice_line(self, cr, uid, picking,
                                       invoice, context=None):
        # TODO: Calcular o valor correto em caso de alteração da quantidade
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

    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move,
                          context=None):

        inv_vals = super(StockPicking, self)._get_invoice_vals(
            cr, uid, key, inv_type, journal_id, move, context=context)

        picking = move.picking_id

        values = {
            'partner_shipping_id': picking.partner_id.id,
            'carrier_id': picking.carrier_id and picking.carrier_id.id,
            'vehicle_id': picking.vehicle_id and picking.vehicle_id.id,
            'weight': picking.weight,
            'weight_net': picking.weight_net,
            'number_of_packages': picking.number_of_packages,
            'incoterm': picking.sale_id.incoterm.id
            if picking.sale_id and picking.sale_id.incoterm.id else False,
        }

        inv_vals.update(values)
        return inv_vals


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _get_invoice_line_vals(self, move, partner, inv_type):
        result = super(StockMove, self)._get_invoice_line_vals(
            move, partner, inv_type)
        if move.procurement_id and move.procurement_id.sale_line_id:
            sale_line = move.procurement_id.sale_line_id

            result.update({
                'insurance_value': sale_line.insurance_value,
                'freight_value': sale_line.freight_value,
                'other_costs_value': sale_line.other_costs_value,
            })

        return result
