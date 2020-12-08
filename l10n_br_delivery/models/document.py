# Copyright (C) 2020 - Gabriel Cardoso de Faria<gabriel.cardoso@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class Document(models.Model):
    _inherit = 'l10n_br_fiscal.document'

    amount_freight_value = fields.Monetary(
        inverse='_inverse_amount_freight_value'
    )

    amount_other_costs_value = fields.Monetary(
        inverse='_inverse_amount_other_costs_value'
    )

    @api.multi
    def _inverse_amount_freight_value(self):
        for record in self.filtered(lambda doc: doc.line_ids):
            amount_freight_value = record.amount_freight_value
            if all(record.line_ids.mapped('freight_value')):
                amount_freight_old = sum(
                    record.line_ids.mapped('freight_value'))
                for line in record.line_ids[:-1]:
                    line.freight_value = amount_freight_value * (
                        line.freight_value / amount_freight_old)
                record.line_ids[-1].freight_value = \
                    amount_freight_value - sum(
                        line.freight_value for line in record.line_ids[:-1])
            else:
                for line in record.line_ids[:-1]:
                    line.freight_value = amount_freight_value * (
                        line.amount_total / record.amount_total)
                record.line_ids[-1].freight_value = \
                    amount_freight_value - sum(
                        line.freight_value for line in record.line_ids[:-1])
            for line in record.line_ids:
                line._onchange_fiscal_taxes()

    @api.multi
    def _inverse_amount_other_costs_value(self):
        for record in self.filtered(lambda doc: doc.line_ids):
            amount_other_costs_value = record.amount_other_costs_value
            if all(record.line_ids.mapped('other_costs_value')):
                amount_freight_old = sum(
                    record.line_ids.mapped('other_costs_value'))
                for line in record.line_ids[:-1]:
                    line.other_costs_value = amount_other_costs_value * (
                        line.other_costs_value / amount_freight_old)
                record.line_ids[-1].other_costs_value = \
                    amount_other_costs_value - sum(
                        line.other_costs_value
                        for line in record.line_ids[:-1])
            else:
                for line in record.line_ids[:-1]:
                    line.other_costs_value = amount_other_costs_value * (
                        line.amount_total / record.amount_total)
                record.line_ids[-1].other_costs_value = \
                    amount_other_costs_value - sum(
                        line.other_costs_value
                        for line in record.line_ids[:-1])
            for line in record.line_ids:
                line._onchange_fiscal_taxes()
