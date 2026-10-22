# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models

BR_CHARTS = ("br_oca", "br_oca_generic")


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _l10n_br_outstanding_account(self, payment_type):
        """The Outstanding Receipts or Payments account the chart created.

        Odoo 17+ leaves the payment method lines without an account and books
        the payment straight on the bank account. The Brazilian chart keeps it
        on the outstanding account until the bank statement reconciles it.
        """
        self.ensure_one()
        if self.company_id.chart_template not in BR_CHARTS:
            return self.env["account.account"]
        xmlid = (
            "account_journal_payment_debit_account_id"
            if payment_type == "inbound"
            else "account_journal_payment_credit_account_id"
        )
        chart = self.with_company(self.company_id).env["account.chart.template"]
        return chart.ref(xmlid, raise_if_not_found=False) or self.env["account.account"]

    def _l10n_br_link_outstanding_accounts(self):
        for journal in self.filtered(lambda j: j.type in ("bank", "cash")):
            for lines, payment_type in (
                (journal.inbound_payment_method_line_ids, "inbound"),
                (journal.outbound_payment_method_line_ids, "outbound"),
            ):
                account = journal._l10n_br_outstanding_account(payment_type)
                if account:
                    lines.filtered(
                        lambda line: not line.payment_account_id
                    ).payment_account_id = account

    @api.depends("type", "currency_id")
    def _compute_inbound_payment_method_line_ids(self):
        super()._compute_inbound_payment_method_line_ids()
        self._l10n_br_link_outstanding_accounts()

    @api.depends("type", "currency_id")
    def _compute_outbound_payment_method_line_ids(self):
        super()._compute_outbound_payment_method_line_ids()
        self._l10n_br_link_outstanding_accounts()
