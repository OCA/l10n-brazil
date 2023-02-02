# Copyright (C) 2023  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _prepare_invoice_vals(self):
        vals = super(PosOrder, self)._prepare_invoice_vals()

        pos_config_id = self.session_id.config_id

        vals.update(
            {
                "document_type_id": pos_config_id.simplified_document_type_id.id,
                "fiscal_operation_id": pos_config_id.out_pos_fiscal_operation_id.id,
                "ind_pres": "1",
                "document_serie_id": pos_config_id.nfce_document_serie_id.id,
                "partner_id": pos_config_id.partner_id.id,
            }
        )

        return vals

    def _generate_pos_order_invoice(self):
        res = super(PosOrder, self)._generate_pos_order_invoice()

        self.account_move.fiscal_document_id.action_document_confirm()

        return res
