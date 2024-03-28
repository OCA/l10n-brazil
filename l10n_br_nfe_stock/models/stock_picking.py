# Copyright 2023 KMEE (Renan Hiroki Bastos <renan.hiroki@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    imported = fields.Boolean(string="Imported")

    origin_document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    linked_document_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.document",
        relation="fiscal_document_picking_rel_1",
        column1="picking_id",
        column2="document_id",
        string="Imported Documents",
        copy=False,
    )

    linked_document_count = fields.Integer(compute="_compute_linked_document_count")

    @api.depends("linked_document_ids")
    def _compute_linked_document_count(self):
        for rec in self:
            rec.linked_document_count = len(rec.linked_document_ids)

    def action_open_document(self):
        result = self.env.ref("l10n_br_nfe_stock.action_document_tree_all").read()[0]
        document_ids = self.mapped("linked_document_ids")

        if len(document_ids) == 1:
            result = self.env.ref("l10n_br_nfe_stock.action_document_form_all").read()[
                0
            ]
            result["res_id"] = document_ids[0].id
        else:
            result["domain"] = "[('id', 'in', %s)]" % (document_ids.ids)

        return result
