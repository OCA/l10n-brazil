# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleDelivery(WebsiteSale):

    def _update_website_sale_delivery_return(self, order, **post):
        carrier_id = int(post['carrier_id'])
        currency = order.currency_id
        if order:
            return {
                'status': order.delivery_rating_success,
                'error_message': order.delivery_message,
                'carrier_id': carrier_id,
                'new_amount_delivery': self._format_amount(
                    order.amount_freight_value, currency),
                'new_amount_untaxed': self._format_amount(
                    order.amount_untaxed, currency),
                'new_amount_tax': self._format_amount(order.amount_tax,
                                                      currency),
                'new_amount_total': self._format_amount(order.amount_total,
                                                        currency),
                }
        return {}
