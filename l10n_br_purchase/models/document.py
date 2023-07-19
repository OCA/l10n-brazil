# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    linked_purchase_ids = fields.Many2many(
        comodel_name="purchase.order",
        relation="fiscal_document_purchase_rel_1",
        column1="document_id",
        column2="purchase_id",
        string="Ordens de Compra",
        copy=False,
    )

    linked_purchase_count = fields.Integer(compute="_compute_linked_purchase_count")

    @api.depends("linked_purchase_ids")
    def _compute_linked_purchase_count(self):
        for rec in self:
            rec.linked_purchase_count = len(rec.linked_purchase_ids)
