# Copyright (C) 2022-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends("move_id.partner_id", "cfop_id", "sale_line_ids")
    def _compute_agent_ids(self):
        # Preserve the agent/commission override coming from the sale order line.
        # In 18.0 account_commission_oca recomputes invoice line agents from the
        # move partner, which overwrites the agents copied from the SO line.
        # When an invoice line is linked to a sale line, keep the SO agents.
        sale_lines = self.filtered(lambda ln: ln.sale_line_ids)
        if sale_lines:
            for line in sale_lines:
                if line.commission_free:
                    line.agent_ids = False
                else:
                    line.agent_ids = [(5, 0, 0)] + [
                        (
                            0,
                            0,
                            {
                                "agent_id": agent.agent_id.id,
                                "commission_id": agent.commission_id.id,
                            },
                        )
                        for sol in line.sale_line_ids
                        for agent in sol.agent_ids
                    ]
        other_lines = self - sale_lines
        if other_lines:
            super(AccountMoveLine, other_lines)._compute_agent_ids()
        for line in self.filtered(
            lambda ln: ln.cfop_id and not ln.cfop_id.finance_move
        ):
            line.agent_ids = False
        return True
