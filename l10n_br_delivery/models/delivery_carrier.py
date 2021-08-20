# Copyright (C) 2010  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class Carrier(models.Model):
    _inherit = 'delivery.carrier'

    antt_code = fields.Char(
        string='Codigo ANTT',
        size=32,
    )

    def rate_shipment(self, order):
        """ Compute the price of the order shipment

        :param order: record of sale.order
        :return dict: {'success': boolean,
                       'price': a float,
                       'error_message': a string containing an error message,
                       'warning_message': a string containing a warning message}
                       # TODO maybe the currency code?
        """
        self.ensure_one()
        res = super().rate_shipment(order)
        # TODO: Localização deveria ter uma maior aderencia
        #  aos metodos do core, mapear melhor os processos,
        #  com dados de demo e testes.
        # Se o Valor Total de Frete estiver preenchido ele tem
        # preferencia sobre o valor Calculado.
        if order.amount_freight_value > 0.0:
            res['price'] = order.amount_freight_value

        return res
