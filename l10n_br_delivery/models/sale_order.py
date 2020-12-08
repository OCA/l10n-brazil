# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_freight = fields.Float(
        inverse='_inverse_amount_freight',
        )


    @api.multi
    def set_delivery_line(self):
        # Remove delivery products from the sales order
        self._remove_delivery_line()

        for order in self:
            if order.state not in ('draft', 'sent'):
                raise UserError(_(
                    'You can add delivery price only on unconfirmed '
                    'quotations.'))
            elif not order.carrier_id:
                raise UserError(_('No carrier set for this order.'))
            elif not order.delivery_rating_success:
                raise UserError(_(
                    'Please use "Check price" in order to compute a shipping '
                    'price for this quotation.'))
            else:
                price_unit = order.carrier_id.rate_shipment(order)['price']
                order.amount_freight = price_unit
        return True

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
                todo = record.env.all.todo.copy()
                record.order_line[-1].freight_value = amount_freight - sum(
                    line.freight_value for line in record.order_line[:-1])
                record.env.all.todo = todo
            for line in record.order_line:
                todo = record.env.all.todo.copy()
                line._onchange_fiscal_taxes()
                record.env.all.todo = todo
