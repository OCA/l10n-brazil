# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# Copyright 2023 KMEE (Renan Hiroki Bastos <renan.hiroki@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    linked_picking_ids = fields.Many2many(
        comodel_name="stock.picking",
        relation="fiscal_document_picking_rel_1",
        column1="document_id",
        column2="picking_id",
        string="Pickings",
        copy=False,
    )

    linked_picking_count = fields.Integer(compute="_compute_linked_picking_count")

    @api.depends("linked_picking_ids")
    def _compute_linked_picking_count(self):
        for rec in self:
            rec.linked_picking_count = len(rec.linked_picking_ids)

    def action_open_picking(self):
        result = self.env.ref("l10n_br_nfe_stock.action_picking_tree_all").read()[0]
        picking_ids = self.mapped("linked_picking_ids")

        if len(picking_ids) == 1:
            result = self.env.ref("l10n_br_nfe_stock.action_picking_form_all").read()[0]
            result["res_id"] = picking_ids[0].id
        else:
            result["domain"] = "[('id', 'in', %s)]" % (picking_ids.ids)

        return result
