# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    imported = fields.Boolean(string="Imported")

    origin_nfe_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Nota de Origem",
        required=False,
    )

    def _prepare_invoice(self):
        return {
            **super()._prepare_invoice(),
            "fiscal_document_id": self.origin_nfe_id.id,
        }


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    origin_nfe_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.line",
        string="Linha na Nota de Origem",
        required=False,
    )
