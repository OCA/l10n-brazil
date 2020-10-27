# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

from parts.odoo.odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def set_delivery_line(self):

        # Remove delivery products from the sales order
        self._remove_delivery_line()

        for order in self:
            if order.state not in ('draft', 'sent'):
                raise UserError(_('You can add delivery price only on unconfirmed quotations.'))
            elif not order.carrier_id:
                raise UserError(_('No carrier set for this order.'))
            elif not order.delivery_rating_success:
                raise UserError(_('Please use "Check price" in order to compute a shipping price for this quotation.'))
            else:
                price_unit = order.carrier_id.rate_shipment(order)['price']
                # TODO check whether it is safe to use delivery_price here
                # todo: get config params to execute compute freight or
                #  create delivery line
                order._compute_freight_distribution()
                # order._create_delivery_line(order.carrier_id, price_unit)
        return True


    @api.multi
    def _compute_freight_distribution(self):
        order_total = 0
        parcial_freight_applied = 0

        amount_freight = self.carrier_id.rate_shipment(self)['price']

        for line in self.order_line:
            if line.product_id.donation:
                continue
            order_total += line.price_total

        for line in self.order_line:
            if line != self.order_line[-1]:
                line_freight = amount_freight * line.price_total/order_total
                line.freight_value = line_freight
                parcial_freight_applied += line_freight
            else:
            # use subtraction for last line
                line.freight_value = amount_freight - parcial_freight_applied



