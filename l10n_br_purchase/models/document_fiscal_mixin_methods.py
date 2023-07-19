# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class FiscalDocumentMixinMethods(models.AbstractModel):
    _inherit = "l10n_br_fiscal.document.mixin.methods"

    def action_open_purchase(self):
        result = self.env.ref("l10n_br_purchase.action_purchase_tree_all").read()[0]
        purchase_ids = self.mapped("linked_purchase_ids")

        if len(purchase_ids) == 1:
            result = self.env.ref("l10n_br_purchase.action_purchase_form_all").read()[0]
            result["res_id"] = purchase_ids[0].id
        else:
            result["domain"] = "[('id', 'in', %s)]" % (purchase_ids.ids)

        return result
