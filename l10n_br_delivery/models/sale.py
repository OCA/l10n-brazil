# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import time

from odoo import models, api, fields, _
from openerp.exceptions import Warning as UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_freight = fields.Float(
        inverse='_inverse_amount_freight',
    )

    @api.model
    def _prepare_invoice(self, order, lines):
        """Prepare the dict of values to create the new invoice for a
           sale order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        result = super(SaleOrder, self)._prepare_invoice(order, lines)

        if order.carrier_id:
            result['carrier_id'] = order.carrier_id.id

        return result

    # TODO Inplement this in object stock.move method _picking_assign
    # def _prepare_order_picking(self, cr, uid, order, context=None):
    #    result = super(SaleOrder, self)._prepare_order_picking(
    #        cr, uid, order, context)
    #
    #    # FIXME - Confirmado bug do OpenERP
    #    # https://bugs.launchpad.net/bugs/1161138
    #    # Esse campo já deveria ser copiado pelo módulo nativo delivery
    #    result['incoterm'] = order.incoterm and order.incoterm.id or False
    #    return result

    @api.multi
    def delivery_set(self):
        # Copia do modulo delivery
        # Exceto pelo final que adiciona ao campo total do frete.

        carrier_obj = self.env['delivery.carrier']
        for order in self:
            carrier = carrier_obj.browse(order.carrier_id.id)
            grid_id = carrier.grid_get(contact_id=order.partner_shipping_id.id)
            if not grid_id:
                raise UserError(_('No Grid Available!'),
                                _('No grid matching for this carrier!'))

            if order.state not in ('draft'):
                raise UserError(_('Order not in Draft State!'),
                                _('The order state have to be draft \
                                  to add delivery lines.'))
            grid = self.env['delivery.grid'].browse(grid_id)

            order.amount_freight = grid.get_price(
                order, time.strftime('%Y-%m-%d'))[0]

    @api.multi
    def _inverse_amount_freight(self):
        for record in self.filtered(lambda so: so.order_line):
            amount_freight = record.amount_freight
            if all(record.order_line.mapped('freight_value')):
                amount_freight_old = sum(
                    record.order_line.mapped('freight_value'))
                for line in record.order_line[:-1]:
                    line.freight_value = amount_freight * (
                        line.freight_value / amount_freight_old)
                record.order_line[-1].freight_value = amount_freight - sum(
                        line.freight_value for line in record.order_line[:-1])
            else:
                amount_total = sum(record.order_line.mapped('price_total'))
                for line in record.order_line[:-1]:
                    line.freight_value = amount_freight * (
                        line.price_total / amount_total)
                record.order_line[-1].freight_value = amount_freight - sum(
                        line.freight_value for line in record.order_line[:-1])
            for line in record.order_line:
                line._onchange_fiscal_taxes()
