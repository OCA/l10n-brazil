# Copyright (C) 2022-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # NOTE: this compute cannot depend on cfop_id directly because
    # _compute_fiscal_tax_ids would trigger it and it would somewho set
    # _compute_tax_fields for recompute loosing possible custom tax values.
    # See https://github.com/OCA/l10n-brazil/issues/4154
    @api.depends("order_id.partner_id", "product_id", "fiscal_operation_line_id")
    def _compute_agent_ids(self):
        res = super()._compute_agent_ids()
        for record in self.filtered(lambda ln: ln.cfop_id):
            if not record.cfop_id.finance_move:
                record.agent_ids = False

        return res
