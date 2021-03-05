# Copyright (C) 2020  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Make Invisible Invoice Button
    button_create_invoice_invisible = fields.Boolean(
        compute='_get_button_create_invoice_invisible'
    )

    @api.depends('state', 'order_line.invoice_status')
    def _get_button_create_invoice_invisible(self):

        button_create_invoice_invisible = False

        if self.company_id.sale_create_invoice_policy == 'stock_picking':
            has_services_to_invoice = self.order_line.filtered(
                lambda x: x.product_id.type == 'service' and
                          x.invoice_status == 'to invoice'
            )
            # A criação de Fatura de Serviços deve ser possível via Pedido
            if not has_services_to_invoice:
                button_create_invoice_invisible = True
        else:
            # No caso da Politica de criação baseada no Pedido de Venda
            # qdo acionado o Botão irá criar as Faturas automaticamente
            # mesmo no caso de ter Produtos e Serviços
            if self.invoice_count > 0:
                button_create_invoice_invisible = True

        # Somente depois do Pedido confirmado o botão pode aparecer
        if self.state != 'sale':
            button_create_invoice_invisible = True

        self.button_create_invoice_invisible = button_create_invoice_invisible
