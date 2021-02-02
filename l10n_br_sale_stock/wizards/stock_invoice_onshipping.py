# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockInvoiceOnshipping(models.TransientModel):

    _inherit = 'stock.invoice.onshipping'

    @api.multi
    def _simulate_invoice_line_onchange(self, values, price_unit=None):
        """
        Simulate onchange for invoice line
        :param values: dict
        :return: dict
        """
        new_values = super()._simulate_invoice_line_onchange(
            values.copy(), price_unit=price_unit)
        line = self.env['account.invoice.line'].new(new_values.copy())
        if price_unit:
            line.price_unit = price_unit
            line._compute_price()
        new_values.update(line._convert_to_write(line._cache))
        values.update(new_values)
        return values

    @api.multi
    def _build_invoice_values_from_pickings(self, pickings):
        """
        Build dict to create a new invoice from given pickings
        :param pickings: stock.picking recordset
        :return: dict
        """
        invoice, values = super()._build_invoice_values_from_pickings(pickings)

        pick = fields.first(pickings)
        if pick.sale_id:
            if pick.sale_id.payment_term_id.id != values['payment_term_id']:
                values.update({
                    'payment_term_id': pick.sale_id.payment_term_id.id,
                })

        return invoice, values
