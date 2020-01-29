# -*- coding: utf-8 -*-
# Copyright (C) 2017  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def _get_invoice_line_vals(self, move, partner, inv_type):
        vals = super(StockMove, self)._get_invoice_line_vals(
            move, partner, inv_type)
        if move.procurement_id and move.procurement_id.sale_line_id:
            vals['partner_order'] = \
                move.procurement_id.sale_line_id.customer_order
            vals['partner_order_line'] = \
                move.procurement_id.sale_line_id.customer_order_line

        return vals

    @api.multi
    def _get_taxes(self, fiscal_position):
        """
        Map product taxes based on given fiscal position
        :param fiscal_position: account.fiscal.position recordset
        :return: account.tax recordset
        """
        product = self.mapped("product_id")
        partner = self.mapped("partner_id")
        product.ensure_one()
        taxes = product.taxes_id
        company_id = self.env.context.get(
            'force_company', self.env.user.company_id.id)
        my_taxes = taxes.filtered(lambda r: r.company_id.id == company_id)

        return fiscal_position.map_tax(my_taxes, product, partner)
