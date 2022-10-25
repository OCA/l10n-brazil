# Copyright (C) 2020  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Make Invisible Invoice Button
    button_create_invoice_invisible = fields.Boolean(
        compute="_compute_get_button_create_invoice_invisible"
    )

    @api.depends("state", "order_line.invoice_status")
    def _compute_get_button_create_invoice_invisible(self):
        button_create_invoice_invisible = False

        lines = self.order_line.filtered(lambda l: l.invoice_status == "to invoice")

        # Somente depois do Pedido confirmado o botão pode aparecer
        if self.state != "sale":
            button_create_invoice_invisible = True
        else:
            if self.company_id.sale_create_invoice_policy == "stock_picking":
                # A criação de Fatura de Serviços deve ser possível via Pedido
                if not any(line.product_id.type == "service" for line in lines):
                    button_create_invoice_invisible = True
            else:
                # No caso da Politica de criação baseada no Pedido de Venda
                # qdo acionado o Botão irá criar as Faturas automaticamente
                # mesmo no caso de ter Produtos e Serviços
                if not lines:
                    button_create_invoice_invisible = True

        self.button_create_invoice_invisible = button_create_invoice_invisible

    @api.onchange("partner_shipping_id")
    def _onchange_partner_shipping_id(self):
        """
        Caso ocorra a alteração do campo Endereço de Entrega/partner_shipping_id
        depois do Pedido confirmado os stock.picking relacionados ficam com o
        partner_id anterior, o que é errado, o metodo original apenas mostra uma
        mensagem de alerta na tela orientando o usuário a corrigir manualmente,
        mas como na localização com esse modulo pode se definir a criação da
        Invoice a partir do stock.picking é melhor garantir a alteração do campo
        partner_id da stock.picking afim de evitar erros na criação da Invoice.
        :return: super()
        """
        # TODO: Verificar essa questão na migração a partir da v14

        pickings = self.picking_ids.filtered(
            lambda p: p.state not in ["done", "cancel"]
            and p.partner_id != self.partner_shipping_id
        )
        # Atribuição da forma abaixo por algum motivo
        # não funciona apenas o write
        # for picking in pickings:
        #    picking.partner_id = self.partner_shipping_id
        pickings.write({"partner_id": self.partner_shipping_id.id})

        return super()._onchange_partner_shipping_id()
