# Copyright (C) 2023 - TODAY Renan Hiroki Bastos - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _create_financial_lines_from_dups(self):
        for invoice in self:
            if invoice.nfe40_dup:
                invoice.financial_move_line_ids = [
                    (2, financial_line, 0)
                    for financial_line in invoice.financial_move_line_ids.ids
                ]
                financial_lines = []
                for dup in invoice.nfe40_dup:
                    financial_lines.append(
                        {
                            "move_id": invoice.id,
                            "name": dup.nfe40_nDup,
                            "debit": 0.0,
                            "credit": dup.nfe40_vDup,
                            "quantity": 1.0,
                            "amount_currency": -dup.nfe40_vDup,
                            "date_maturity": dup.nfe40_dVenc,
                            "currency_id": invoice.currency_id.id,
                            "account_id": invoice.partner_id.property_account_payable_id.id,
                            "partner_id": invoice.partner_id.id,
                            "exclude_from_invoice_tab": True,
                        }
                    )
                invoice.financial_move_line_ids = [
                    (0, 0, dup) for dup in financial_lines
                ]
