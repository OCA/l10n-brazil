# Copyright (C) 2020  Magno Costa - Akretion
# Copyright (C) 2020  Renato Lima - Akretion
# Copyright 2023 KMEE (Renan Hiroki Bastos <renan.hiroki@kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("purchase_vendor_bill_id", "purchase_id")
    def _onchange_purchase_auto_complete(self):
        if self.purchase_id:
            if self.purchase_id.fiscal_operation_id:
                self.fiscal_operation_id = self.purchase_id.fiscal_operation_id
                if not self.document_type_id:
                    # Testes não passam por aqui, qual seria esse caso de uso?
                    # Porque se não houver o codigo pode ser removido
                    self.document_type_id = self.company_id.document_type_id
        return super()._onchange_purchase_auto_complete()

    def action_open_purchase(self):
        result = self.env.ref("l10n_br_nfe_stock.action_purchase_tree_all").read()[0]
        purchase_ids = self.mapped("linked_purchase_ids")

        if len(purchase_ids) == 1:
            result = self.env.ref("l10n_br_nfe_stock.action_purchase_form_all").read()[
                0
            ]
            result["res_id"] = purchase_ids[0].id
        else:
            result["domain"] = "[('id', 'in', %s)]" % (purchase_ids.ids)

        return result
