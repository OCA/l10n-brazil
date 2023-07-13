# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    imported = fields.Boolean(string="Imported")

    origin_document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    def _prepare_invoice(self):
        return {
            **super()._prepare_invoice(),
            "fiscal_document_id": self.origin_document_id.id,
            "document_type_id": self.origin_document_id.document_type_id.id,
        }

    def confirm_and_create_invoice(self):
        self.button_confirm()

        self.env["stock.immediate.transfer"].with_context(
            default_pick_ids=self.picking_ids,
            button_validate_picking_ids=self.picking_ids.ids,
        ).create({}).process()

        self.action_create_invoice()


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    origin_document_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.line"
    )
