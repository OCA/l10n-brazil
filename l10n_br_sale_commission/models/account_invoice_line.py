# Copyright (C) 2022-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.onchange("fiscal_operation_line_id")
    def _onchange_fiscal_operation_line_id(self):
        """
        Caso a Linha da Operação Fiscal Não Gera Financeiro
        não deve existir Comissão
        """
        super()._onchange_fiscal_operation_line_id()
        for record in self:
            if record.cfop_id and not record.cfop_id.finance_move:
                record.agent_ids = False
