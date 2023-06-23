# Copyright (C) 2023  Felipe Zago Rodrigues - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

from odoo import api, fields, models


class NfeImport(models.TransientModel):
    _inherit = "l10n_br_nfe.import_xml"

    purchase_link_type = fields.Selection(
        selection=[
            ("choose", "Choose"),
            ("create", "Create"),
        ],
        default="choose",
        string="Purchase Link Type",
    )

    purchase_id = fields.Many2one(
        comodel_name="purchase.order",
        string="Purchase Order",
        required=False,
        default=False,
        domain=False,
    )

    @api.onchange("partner_cpf_cnpj")
    def _onchange_partner_cpf_cnpj(self):
        domain = {}
        if self.partner_cpf_cnpj:
            supplyer_id = self.env["res.partner"].search(
                [("cnpj_cpf", "=", self.partner_cpf_cnpj)]
            )
            purchase_order_ids = self.env["purchase.order"].search(
                [
                    ("partner_id", "=", supplyer_id.id),
                    ("state", "not in", ["done", "cancel"]),
                ]
            )

            domain = {"purchase_id": [("id", "in", purchase_order_ids.ids)]}
        return {"domain": domain}

    def _create_edoc_from_xml(self):
        edoc = super()._create_edoc_from_xml()

        if not self.purchase_id and self.purchase_link_type == "create":
            self.purchase_id = self._create_purchase_order(edoc)

        return edoc

    def _create_purchase_order(self, document):
        self.set_fields_data_by_xml()

        company = self.env.user.company_id
        purchase = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_id.id,
                "currency_id": company.currency_id.id,
                "fiscal_operation_id": company.purchase_fiscal_operation_id.id,
                "date_order": datetime.now(),
                "origin_nfe_id": document.id,
                "imported": True,
            }
        )
        document.linked_purchase_ids = [(4, purchase.id)]

        purchase_lines = []
        for line in document.fiscal_line_ids:
            product_uom = line.uom_id or line.product_id.uom_id
            purchase_line = self.env["purchase.order.line"].create(
                {
                    "product_id": line.product_id.id,
                    "origin_nfe_line_id": line.id,
                    "name": line.product_id.display_name,
                    "date_planned": datetime.now(),
                    "product_qty": line.quantity,
                    "product_uom": product_uom.id,
                    "price_unit": line.price_unit,
                    "price_subtotal": line.amount_total,
                    "order_id": purchase.id,
                }
            )
            purchase_lines.append(purchase_line.id)
        purchase.write({"order_line": [(6, 0, purchase_lines)]})
        purchase.button_confirm()
        return purchase
