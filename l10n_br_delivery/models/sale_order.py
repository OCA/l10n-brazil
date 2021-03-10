# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_freight_value = fields.Monetary(
        inverse='_inverse_amount_freight',
    )

    amount_insurance_value = fields.Monetary(
        inverse='_inverse_amount_insurance',
        readonly=False,
    )

    amount_other_value = fields.Monetary(
        inverse='_inverse_amount_other',
        readonly=False,
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
                order.amount_freight_value = price_unit
        return True

    @api.multi
    def _inverse_amount_freight(self):
        for record in self.filtered(lambda so: so.order_line):
            amount_freight_value = record.amount_freight_value
            if all(record.order_line.mapped('freight_value')):
                amount_freight_old = sum(
                    record.order_line.mapped('freight_value'))
                for line in record.order_line[:-1]:
                    line.freight_value = amount_freight_value * (
                        line.freight_value / amount_freight_old)
                record.order_line[-1].freight_value = (
                    amount_freight_value -
                    sum(line.freight_value
                        for line in record.order_line[:-1])
                )
            else:
                amount_total = sum(record.order_line.mapped('price_total'))
                for line in record.order_line[:-1]:
                    line.freight_value = amount_freight_value * (
                        line.price_total / amount_total)
                record.order_line[-1].freight_value = (
                    amount_freight_value -
                    sum(line.freight_value for line in record.order_line[:-1])
                )
            for line in record.order_line:
                line._onchange_fiscal_taxes()
            record._fields['amount_total'].compute_value(record)
            record.write({
                name: value
                for name, value in record._cache.items()
                if record._fields[name].compute == '_amount_all' and
                not record._fields[name].inverse
            })

    @api.multi
    def _inverse_amount_insurance(self):
        for record in self.filtered(lambda so: so.order_line):
            amount_insurance_value = record.amount_insurance_value
            if all(record.order_line.mapped('insurance_value')):
                amount_insurance_old = sum(
                    record.order_line.mapped('insurance_value'))
                for line in record.order_line[:-1]:
                    line.insurance_value = amount_insurance_value * (
                        line.insurance_value / amount_insurance_old)
                record.order_line[-1].insurance_value = \
                    amount_insurance_value - sum(
                        line.insurance_value
                        for line in record.order_line[:-1]
                    )
            else:
                amount_total = sum(record.order_line.mapped('price_total'))
                for line in record.order_line[:-1]:
                    line.insurance_value = amount_insurance_value * (
                        line.price_total / amount_total)
                record.order_line[-1].insurance_value = \
                    amount_insurance_value - sum(
                        line.insurance_value
                        for line in record.order_line[:-1])
            for line in record.order_line:
                line._onchange_fiscal_taxes()
            record._fields['amount_total'].compute_value(record)
            record.write({
                name: value
                for name, value in record._cache.items()
                if record._fields[name].compute == '_amount_all' and
                not record._fields[name].inverse
            })

    @api.multi
    def _inverse_amount_other(self):
        for record in self.filtered(lambda so: so.order_line):
            amount_other_value = record.amount_other_value
            if all(record.order_line.mapped('other_value')):
                amount_other_old = sum(
                    record.order_line.mapped('other_value'))
                for line in record.order_line[:-1]:
                    line.other_value = amount_other_value * (
                        line.other_value / amount_other_old)
                record.order_line[-1].other_value = (
                    amount_other_value -
                    sum(line.other_value
                        for line in record.order_line[:-1])
                )
            else:
                amount_total = sum(record.order_line.mapped('price_total'))
                for line in record.order_line[:-1]:
                    line.other_value = amount_other_value * (
                        line.price_total / amount_total)
                record.order_line[-1].other_value = (
                    amount_other_value -
                    sum(line.other_value
                        for line in record.order_line[:-1])
                )
            for line in record.order_line:
                line._onchange_fiscal_taxes()
            record._fields['amount_total'].compute_value(record)
            record.write({
                name: value
                for name, value in record._cache.items()
                if record._fields[name].compute == '_amount_all' and
                not record._fields[name].inverse
            })
