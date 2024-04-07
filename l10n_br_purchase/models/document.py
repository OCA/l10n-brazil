# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# Copyright 2023 KMEE (Renan Hiroki Bastos <renan.hiroki@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    linked_purchase_ids = fields.Many2many(
        comodel_name="purchase.order",
        relation="fiscal_document_purchase_rel_1",
        column1="document_id",
        column2="purchase_id",
        string="Purchase Orders",
        copy=False,
    )

    linked_purchase_count = fields.Integer(compute="_compute_linked_purchase_count")

    @api.depends("linked_purchase_ids")
    def _compute_linked_purchase_count(self):
        for rec in self:
            rec.linked_purchase_count = len(rec.linked_purchase_ids)

    def action_open_purchase(self):
        result = self.env.ref("purchase.action_purchase_tree_all").read()[0]
        purchase_ids = self.mapped("linked_purchase_ids")

        if len(purchase_ids) == 1:
            result = self.env.ref("purchase.action_purchase_form_all").read()[0]
            result["res_id"] = purchase_ids[0].id
        else:
            result["domain"] = "[('id', 'in', %s)]" % (purchase_ids.ids)

        return result
