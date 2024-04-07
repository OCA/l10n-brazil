# Copyright 2023 KMEE (Renan Hiroki Bastos <renan.hiroki@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_open_picking(self):
        result = self.env.ref("l10n_br_nfe_stock.action_picking_tree_all").read()[0]
        picking_ids = self.mapped("linked_picking_ids")

        if len(picking_ids) == 1:
            result = self.env.ref("l10n_br_nfe_stock.action_picking_form_all").read()[0]
            result["res_id"] = picking_ids[0].id
        else:
            result["domain"] = "[('id', 'in', %s)]" % (picking_ids.ids)

        return result
