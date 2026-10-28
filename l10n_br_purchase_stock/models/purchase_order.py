# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    purchase_invoicing_policy = fields.Selection(
        related="company_id.purchase_invoicing_policy",
    )

    # Make Invisible Invoice Button
    button_create_invoice_invisible = fields.Boolean(
        compute="_compute_get_button_create_invoice_invisible"
    )

    @api.depends("state", "invoice_status")
    def _compute_get_button_create_invoice_invisible(self):
        for record in self:
            button_create_invoice_invisible = False

            # Somente depois do Pedido confirmado o botão pode aparecer
            if (
                record.state not in ("purchase", "done")
                or record.invoice_status != "to invoice"
                or not record.order_line
            ):
                button_create_invoice_invisible = True
            else:
                if record.purchase_invoicing_policy == "stock_picking":
                    # A criação de Fatura de Serviços deve ser possível via Pedido
                    if not any(
                        line.product_id.type == "service" for line in record.order_line
                    ):
                        button_create_invoice_invisible = True

            record.button_create_invoice_invisible = button_create_invoice_invisible

    @api.model
    def _prepare_picking(self):
        values = super()._prepare_picking()
        if self.fiscal_operation_id:
            values.update(self._prepare_br_fiscal_dict())
        else:
            values["fiscal_operation_id"] = False
        if self.company_id.purchase_invoicing_policy == "stock_picking":
            values["invoice_state"] = "2binvoiced"
        return values
