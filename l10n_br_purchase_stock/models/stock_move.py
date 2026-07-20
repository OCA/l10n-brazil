# @ 2021 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.tools import float_compare


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_price_unit_invoice(self, inv_type, partner, qty=1):
        result = super()._get_price_unit_invoice(inv_type, partner, qty)
        # Caso tenha Purchase Line já vem desagrupado aqui devido ao KEY
        if len(self) == 1:
            # Caso venha apenas uma linha porem sem
            # purchase_line_id é preciso ignora-la
            if self.purchase_line_id and self.purchase_line_id.price_unit != result:
                result = self.purchase_line_id.price_unit

        return result

    def _get_price_unit(self):
        """Fatura-antes-do-recebimento (caso brasileiro típico: a NF acompanha
        a mercadoria e é lançada antes do picking): o custo de valorização deve
        vir do custo LÍQUIDO da NF real (stock_cost_unit das linhas da fatura,
        que herdam o mixin fiscal via _inherits), não do estimado do pedido.

        O super() (l10n_br_stock_account) já devolve o stock_cost_unit do
        move — que reflete o PO; aqui refinamos com a fatura quando ela
        existe, espelhando a condição do core purchase_stock."""
        self.ensure_one()
        result = super()._get_price_unit()
        if (
            not self.fiscal_operation_id
            or self.fiscal_operation_id.fiscal_operation_type != "in"
            or self._should_ignore_pol_price()
        ):
            return result

        line = self.purchase_line_id
        received_qty = line.qty_received
        if self.state == "done":
            received_qty -= self.product_uom._compute_quantity(
                self.quantity_done, line.product_uom, rounding_method="HALF-UP"
            )
        if (
            line.product_id.purchase_method == "purchase"
            and float_compare(
                line.qty_invoiced,
                received_qty,
                precision_rounding=line.product_uom.rounding,
            )
            > 0
        ):
            posted_lines = line.sudo().invoice_lines.filtered(
                lambda il: il.move_id.state == "posted"
            )
            quantity = 0.0
            value = 0.0
            for inv_line in posted_lines:
                qty = inv_line.product_uom_id._compute_quantity(
                    inv_line.quantity, line.product_id.uom_id
                )
                unit_cost = inv_line.stock_cost_unit
                if inv_line.currency_id != self.company_id.currency_id:
                    unit_cost = inv_line.currency_id._convert(
                        unit_cost,
                        self.company_id.currency_id,
                        self.company_id,
                        inv_line.move_id.invoice_date or inv_line.move_id.date,
                        round=False,
                    )
                value += unit_cost * qty
                quantity += qty
            if quantity:
                result = value / quantity

        return result
