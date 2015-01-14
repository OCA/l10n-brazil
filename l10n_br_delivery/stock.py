# -*- coding: utf-8 -*-
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

    #TODO migrate to new API
    def _prepare_shipping_invoice_line(self, cr, uid, picking,
                                    invoice, context=None):
        #TODO: Calcular o valor correto em caso de alteração da quantidade
        return False

    @api.model
    def _create_invoice_from_picking(self, picking, vals):

        invoice_vals = {
            'partner_shipping_id': picking.partner_id.id,
            'carrier_id': picking.carrier_id and picking.carrier_id.id,
            'vehicle_id': picking.vehicle_id and picking.vehicle_id.id,
            'incoterm': picking.incoterm.id,
            'weight': picking.weight,
            'weight_net': picking.weight_net,
            'number_of_packages': picking.number_of_packages,
        }

        vals.update(invoice_vals)
        invoice_id = super(StockPicking, self)._create_invoice_from_picking(
            picking, vals)

        invoice = self.env['account.invoice'].browse(invoice_id)
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        costs = [
            ('Frete', company.account_freight_id, invoice.amount_freight),
            ('Seguro', company.account_insurance_id, invoice.amount_insurance),
            ('Outros Custos', company.account_other_costs, invoice.amount_costs)
        ]

        ait_obj = self.env['account.invoice.tax']
        for cost in costs:
            if cost[2] > 0:
                tax_values = {
                    'invoice_id': invoice.id,
                    'name': cost[0],
                    'account_id': cost[1].id,
                    'amount': cost[2],
                    'base': cost[2],
                    'manual': True,
                    'company_id': company.id,
                }

                ait_obj.create(tax_values)
        return invoice_id


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _get_invoice_line_vals(self, move, partner, inv_type):
        result = super(StockMove, self)._get_invoice_line_vals(
            move, partner, inv_type)

        if move.procurement_id.sale_line_id:
            result['insurance_value'] = move.procurement_id.sale_line_id.insurance_value
            result['other_costs_value'] = move.procurement_id.sale_line_id.other_costs_value
            result['freight_value'] = move.procurement_id.sale_line_id.freight_value

        return result