# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

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
                order.amount_freight_value = price_unit
        return True

    # TODO: Deveria exisitr o Peso Total Liquido e Peso Total Bruto como era na
    #  v8, aparetemente agora so existe o campo weight no cadastro do Produto
    amount_weight = fields.Float(
        string=_('Amount Weight'),
        compute='_compute_amount_weight'
    )

    amount_volume = fields.Float(
        string=_('Amount Volume'),
        compute='_compute_amount_volume'
    )

    def _compute_amount_weight(self):

        for record in self:
            amount_weight = 0.0
            for l in record.order_line:
                amount_weight += l.product_qty * l.product_id.weight
            record.amount_weight = amount_weight

    def _compute_amount_volume(self):

        for record in self:
            amount_volume = 0.0
            for l in record.order_line:
                amount_volume += l.product_qty * l.product_id.volume
            record.amount_volume = amount_volume
