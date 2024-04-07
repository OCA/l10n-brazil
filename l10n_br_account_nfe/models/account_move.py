# Copyright 2023 Akretion (Raphaẽl Valyi <raphael.valyi@akretion.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models
from odoo.tools import float_compare


class AccountMove(models.Model):
    _inherit = "account.move"

    def _recompute_payment_terms_lines(self):
        self.ensure_one()
        if (
            self.imported_document
            and self.nfe40_dup
            and float_compare(
                sum(self.invoice_line_ids.mapped("debit")),
                sum(self.nfe40_dup.mapped("nfe40_vDup")),
                2,
            )
            == 0  # only trigger when all NFe lines are added
        ):
            # just like in the original method, remove old terms:
            existing_terms_lines = self.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type
                in ("receivable", "payable")
            )
            self.line_ids -= existing_terms_lines

            if self != self._origin:  # is it a draft move?
                create_method = self.env["account.move.line"].new
            else:
                create_method = self.env["account.move.line"].create

            if self.is_sale_document(include_receipts=True) and self.partner_id:
                dup_account = (
                    self.partner_id.commercial_partner_id.property_account_receivable_id
                )
            else:
                dup_account = (
                    self.partner_id.commercial_partner_id.property_account_payable_id
                )

            for dup in self.nfe40_dup:
                create_method(
                    {
                        "move_id": self.id,
                        "name": dup.nfe40_nDup,
                        "debit": 0.0,
                        "credit": dup.nfe40_vDup,
                        "quantity": 1.0,
                        "amount_currency": -dup.nfe40_vDup,
                        "date_maturity": dup.nfe40_dVenc,
                        "currency_id": self.currency_id.id,
                        "account_id": dup_account.id,
                        "partner_id": self.partner_id.id,
                        "exclude_from_invoice_tab": True,
                    }
                )
        else:
            return super()._recompute_payment_terms_lines()
