# Copyright (C) 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    FISCAL_PAYMENT_MODE,
    MODELO_FISCAL_NFCE,
)


class AccountMove(models.Model):

    _inherit = "account.move"

    def view_pdf(self):
        self.ensure_one()
        if self.document_type != MODELO_FISCAL_NFCE:
            return super(AccountMove, self).view_pdf()

        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", "l10n_br_pos_nfce.report_danfe_nfce")],
                limit=1,
            )
            .report_action(self, data=self._prepare_nfce_danfe_values())
        )

    def _prepare_nfce_danfe_values(self):
        return {
            "company_ie": self.company_inscr_est,
            "company_cnpj": self.company_cnpj_cpf,
            "company_legal_name": self.company_legal_name,
            "company_street": self.company_street,
            "company_number": self.company_number,
            "company_district": self.company_district,
            "company_city": self.company_city_id.display_name,
            "company_state": self.company_state_id.name,
            "lines": self._prepare_nfce_danfe_line_values(),
            "total_product_quantity": len(
                self.line_ids.filtered(lambda line: line.product_id)
            ),
            "amount_total": self.amount_total,
            "amount_discount_value": self.amount_discount_value,
            "amount_freight_value": self.amount_freight_value,
            "payments": self._prepare_nfce_danfe_payment_values(),
            "amount_change": self.nfe40_vTroco,
            "nfce_url": self.fiscal_document_id.get_nfce_qrcode_url(),
            "document_key": self.document_key,
            "document_number": self.document_number,
            "document_serie": self.document_serie,
            "document_date": self.document_date.astimezone().strftime(
                "%d/%m/%y %H:%M:%S"
            ),
            "authorization_protocol": self.authorization_protocol,
            "document_qrcode": self.fiscal_document_id.get_nfce_qrcode(),
            "system_env": self.nfe40_tpAmb,
            "unformatted_amount_freight_value": self.amount_freight_value,
            "unformatted_amount_discount_value": self.amount_discount_value,
            "contingency": self.nfe_transmission != "1",
            "homologation_environment": self.nfe_environment == "2",
        }

    def _prepare_nfce_danfe_line_values(self):
        lines_list = []
        lines = self.line_ids.filtered(lambda line: line.product_id)
        for index, line in enumerate(lines):
            product_id = line.product_id
            lines_list.append(
                {
                    "product_index": index + 1,
                    "product_default_code": product_id.default_code,
                    "product_name": product_id.name,
                    "product_quantity": line.quantity,
                    "product_uom": product_id.uom_name,
                    "product_unit_value": product_id.lst_price,
                    "product_unit_total": line.quantity * product_id.lst_price,
                }
            )
        return lines_list

    def _prepare_nfce_danfe_payment_values(self):
        payments_list = []
        for payment in self.nfe40_detPag:
            payments_list.append(
                {
                    "method": dict(FISCAL_PAYMENT_MODE)[payment.nfe40_tPag],
                    "value": payment.nfe40_vPag,
                }
            )
        return payments_list


# class AccountMoveLine(models.Model):
#    _inherit = "account.move.line"
#
#    #
#    # @override
#    #
#    # The method was overwritten due to the need for it to also accept cancelled
#    # orders on validation.
#    #
#    def reconcile(self):
#        results = {}
#
#        if not self:
#            return results
#
#        # List unpaid invoices
#        not_paid_invoices = self.move_id.filtered(
#            lambda move: move.is_invoice(include_receipts=True)
#            and move.payment_state not in ("paid", "in_payment")
#        )
#
#        # ==== Check the lines can be reconciled together ====
#        company = None
#        account = None
#        for line in self:
#            if line.reconciled:
#                raise UserError(
#                    _(
#                        "You are trying to reconcile some entries that are already reconciled."
#                    )
#                )
#            if (
#                not line.account_id.reconcile
#                and line.account_id.internal_type != "liquidity"
#            ):
#                raise UserError(
#                    _(
#                        "Account %s does not allow reconciliation. First change the configuration of this account to allow it."  # noqa: B950
#                    )
#                    % line.account_id.display_name
#                )
#            if line.move_id.state not in ["posted", "cancel"]:
#                raise UserError(_("You can only reconcile posted entries."))
#            if company is None:
#                company = line.company_id
#            elif line.company_id != company:
#                raise UserError(
#                    _("Entries doesn't belong to the same company: %s != %s")
#                    % (company.display_name, line.company_id.display_name)
#                )
#            if account is None:
#                account = line.account_id
#            elif line.account_id != account:
#                raise UserError(
#                    _("Entries are not from the same account: %s != %s")
#                    % (account.display_name, line.account_id.display_name)
#                )
#
#        sorted_lines = self.sorted(
#            key=lambda line: (line.date_maturity or line.date, line.currency_id)
#        )
#
#        # ==== Collect all involved lines through the existing reconciliation ====
#
#        involved_lines = sorted_lines
#        involved_partials = self.env["account.partial.reconcile"]
#        current_lines = involved_lines
#        current_partials = involved_partials
#        while current_lines:
#            current_partials = (
#                current_lines.matched_debit_ids + current_lines.matched_credit_ids
#            ) - current_partials
#            involved_partials += current_partials
#            current_lines = (
#                current_partials.debit_move_id + current_partials.credit_move_id
#            ) - current_lines
#            involved_lines += current_lines
#
#        # ==== Create partials ====
#
#        partials = self.env["account.partial.reconcile"].create(
#            sorted_lines._prepare_reconciliation_partials()
#        )
#
#        # Track newly created partials.
#        results["partials"] = partials
#        involved_partials += partials
#
#        # ==== Create entries for cash basis taxes ====
#
#        is_cash_basis_needed = (
#            account.company_id.tax_exigibility
#            and account.user_type_id.type in ("receivable", "payable")
#        )
#        if is_cash_basis_needed and not self._context.get("move_reverse_cancel"):
#            tax_cash_basis_moves = partials._create_tax_cash_basis_moves()
#            results["tax_cash_basis_moves"] = tax_cash_basis_moves
#
#        # ==== Check if a full reconcile is needed ====
#
#        if involved_lines[0].currency_id and all(
#            line.currency_id == involved_lines[0].currency_id for line in involved_lines
#        ):
#            is_full_needed = all(
#                line.currency_id.is_zero(line.amount_residual_currency)
#                for line in involved_lines
#            )
#        else:
#            is_full_needed = all(
#                line.company_currency_id.is_zero(line.amount_residual)
#                for line in involved_lines
#            )
#
#        if is_full_needed:
#
#            # ==== Create the exchange difference move ====
#
#            if self._context.get("no_exchange_difference"):
#                exchange_move = None
#            else:
#                exchange_move = involved_lines._create_exchange_difference_move()
#                if exchange_move:
#                    exchange_move_lines = exchange_move.line_ids.filtered(
#                        lambda line: line.account_id == account
#                    )
#
#                    # Track newly created lines.
#                    involved_lines += exchange_move_lines
#
#                    # Track newly created partials.
#                    exchange_diff_partials = (
#                        exchange_move_lines.matched_debit_ids
#                        + exchange_move_lines.matched_credit_ids
#                    )
#                    involved_partials += exchange_diff_partials
#                    results["partials"] += exchange_diff_partials
#
#                    exchange_move._post(soft=False)
#
#            # ==== Create the full reconcile ====
#
#            results["full_reconcile"] = self.env["account.full.reconcile"].create(
#                {
#                    "exchange_move_id": exchange_move and exchange_move.id,
#                    "partial_reconcile_ids": [(6, 0, involved_partials.ids)],
#                    "reconciled_line_ids": [(6, 0, involved_lines.ids)],
#                }
#            )
#
#        # Trigger action for paid invoices
#        not_paid_invoices.filtered(
#            lambda move: move.payment_state in ("paid", "in_payment")
#        ).action_invoice_paid()
#
#        return results
#
