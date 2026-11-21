# Copyright (C) 2020  Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# Copyright (C) 2021  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_new_picking_values(self):
        # IMPORTANTE: a sequencia de update dos dicionarios quando o
        # partner_shipping_id é diferente, o metodo do fiscal está
        # sobre escrevendo o partner_id e acaba criando um picking
        # sem o partner_id caso esse dict atualize o do super
        values = {}
        fiscal_operation = False
        if self.sale_line_id:
            if self.sale_line_id.order_id.fiscal_operation_id:
                fiscal_operation = self.sale_line_id.order_id.fiscal_operation_id
                values = self.sale_line_id.order_id._prepare_br_fiscal_dict()

        values.update(super()._get_new_picking_values())
        # self is a recordset, possibly with different fiscal operations
        # so we use the fiscal_operation from the SO for the picking:
        if fiscal_operation:
            values.update({"fiscal_operation_id": fiscal_operation.id})

        return values

    def _get_fiscal_partner(self):
        """
        Use partner_invoice_id if different from partner
        """
        self.ensure_one()
        partner = super()._get_fiscal_partner()
        if self.sale_line_id:
            if partner != self.sale_line_id.order_id.partner_invoice_id:
                partner = self.sale_line_id.order_id.partner_invoice_id
        return partner

    def _get_price_unit_invoice(self, inv_type, partner, qty=1):
        """A sold move is invoiced at the price of the sale.

        l10n_br_stock_account invoices the outgoing moves without a price
        informed at the cost of the product (simples remessa and so on), and
        whether it overrides the sale price of sale_stock_picking_invoicing
        depends on the order the modules are loaded in.
        """
        result = super()._get_price_unit_invoice(inv_type, partner, qty)
        move = fields.first(self)
        line = move.sale_line_id
        if not line or inv_type not in ("out_invoice", "out_refund"):
            return result
        if move.price_unit > 0.0:
            # price informed by the user on the move has priority
            return result
        if move.product_id != line.product_id and hasattr(
            move, "_get_kit_component_price_unit"
        ):
            # component of a phantom kit: its share of the kit price
            return move._get_kit_component_price_unit()
        return line.price_unit
