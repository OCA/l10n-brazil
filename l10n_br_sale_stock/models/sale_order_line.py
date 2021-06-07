# Copyright (C) 2013  Raphaël Valyi - Akretion
# Copyright (C) 2014  Renato Lima - Akretion
# Copyright (C) 2021  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_procurement_values(self, group_id=False):
        values = self._prepare_br_fiscal_dict()
        values.update(super()._prepare_procurement_values(group_id))
        # Incluir o invoice_state
        if self.order_id.company_id.sale_create_invoice_policy == "stock_picking":
            values["invoice_state"] = "2binvoiced"

        return values

    # no trigger product_id.invoice_policy to avoid retroactively changing SO
    @api.depends("qty_invoiced", "qty_delivered", "product_uom_qty", "order_id.state")
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order,
        the quantity to invoice is calculated from the ordered quantity.
        Otherwise, the quantity delivered is used.
        """
        super()._get_to_invoice_qty()

        for line in self:
            if line.order_id.state in ["sale", "done"]:
                if line.product_id.invoice_policy == "order":
                    if (
                        line.order_id.company_id.sale_create_invoice_policy
                        == "stock_picking"
                        and line.product_id.type == "product"
                    ):
                        # O correto seria que ao selecionar
                        # sale_create_invoice_policy 'stock_picking' os
                        # produtos tenham o campo invoice_policy definidos para
                        # 'delivery', porém para evitar que seja criada uma
                        # Fatura a partir do Pedido de Venda estamos
                        # alterando isso mesmo para os produtos definidos com
                        # 'order', já que a Politica de Criação da Fatura no
                        # caso do Tipo Produto está definida para ser a
                        # partir do stock.picking .
                        # TODO: Essa seria a melhor opção ? Por enquanto pelo
                        #  que vi para ter o mesmo resultado, que é no caso
                        #  sale_create_invoice_policy 'stock_picking' só ser
                        #  possível criar a partir do sale.order Faturas das
                        #  linhas que sejam type service sim, a outra opção
                        #  seria sobre escrever o metodo action_invoice_create
                        #  sem ser possível chamar o super.
                        line.qty_to_invoice = 0
