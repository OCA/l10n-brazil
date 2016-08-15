# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

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

    @api.model
    def _create_invoice_from_picking(self, picking, vals):

        vals.update({
            'carrier_id': picking.carrier_id and picking.carrier_id.id,
            'vehicle_id': picking.vehicle_id and picking.vehicle_id.id,
            'weight': picking.weight,
            'weight_net': picking.weight_net,
            'number_of_packages': picking.number_of_packages,
            'incoterm': picking.sale_id.incoterm.id
            if picking.sale_id and picking.sale_id.incoterm.id else False,
        })
        return super(StockPicking, self)._create_invoice_from_picking(
            picking, vals)


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
