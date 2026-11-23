# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from contextlib import contextmanager
from datetime import date
from unittest import mock

from odoo import Command

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon
from odoo.addons.l10n_br_fiscal_edi.tools import EdiInstallment

DUE_LINE_ACCOUNT_TYPES = ("asset_receivable", "liability_payable")


class AccountEdiCase(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.company = cls.env.company
        cls.supplier = cls.partner_a
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")
        cls.product = cls.env["product.product"].create(
            {"name": "Imported service", "type": "service"}
        )
        cls.payment_term = cls.env["account.payment.term"].create(
            {
                "name": "Two installments",
                "line_ids": [
                    Command.create(
                        {"value": "percent", "value_amount": 50.0, "days": 30}
                    ),
                    Command.create(
                        {"value": "balance", "value_amount": 0.0, "days": 60}
                    ),
                ],
            }
        )

    def _imported_document(self, **line_values):
        """A reviewed imported document of 1000.00, with a single line."""
        values = {
            "name": "Imported line",
            "product_id": self.product.id,
            "uom_id": self.product.uom_id.id,
            "quantity": 1,
            "price_unit": 1000.0,
            "fiscal_operation_type": "in",
            "fiscal_operation_id": self.operation.id,
            "fiscal_operation_line_id": self.operation_line.id,
            "import_state": "resolved",
        }
        values.update(line_values)
        return self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_SE").id,
                "document_serie": "1",
                "document_number": "100",
                "issuer": "partner",
                "partner_id": self.supplier.id,
                "fiscal_operation_id": self.operation.id,
                "fiscal_operation_type": "in",
                "document_date": "2026-01-10 12:00:00",
                "imported_document": True,
                "fiscal_line_ids": [Command.create(values)],
            }
        )

    def _own_imported_document(self, confirm=True, with_serie=True, **values):
        """A note the company issued in another system, imported and authorized.
        The series of the file is the text of document_serie; the company may
        have no series record of the type (with_serie=False)."""
        document_type = self.env.ref("l10n_br_fiscal.document_SE")
        series = self.env["l10n_br_fiscal.document.serie"].search(
            [
                ("document_type_id", "=", document_type.id),
                ("company_id", "=", self.company.id),
            ]
        )
        series.active = False
        serie = self.env["l10n_br_fiscal.document.serie"]
        if with_serie:
            serie = serie.create(
                {
                    "code": "001",
                    "name": "Series 1",
                    "document_type_id": document_type.id,
                    "company_id": self.company.id,
                }
            )
        operation = self.env.ref("l10n_br_fiscal.fo_venda")
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": document_type.id,
                "document_serie_id": serie.id,
                "document_serie": "001",
                "document_number": "777",
                "issuer": "company",
                "partner_id": self.partner_a.id,
                "fiscal_operation_id": operation.id,
                "fiscal_operation_type": "out",
                "document_date": "2026-01-10 12:00:00",
                "imported_document": True,
                **values,
                "fiscal_line_ids": [
                    Command.create(
                        {
                            "name": "Imported line",
                            "product_id": self.product_a.id,
                            "uom_id": self.product_a.uom_id.id,
                            "quantity": 1,
                            "price_unit": 1000.0,
                            "fiscal_operation_type": "out",
                            "fiscal_operation_id": operation.id,
                            "fiscal_operation_line_id": self.env.ref(
                                "l10n_br_fiscal.fo_venda_servico"
                            ).id,
                            "import_state": "resolved",
                        }
                    )
                ],
            }
        )
        if confirm:
            document._trigger_fsm("action_confirm_imported")
        return document

    @contextmanager
    def _declared(self, *installments):
        """The document declares these installments: (due date, amount)."""
        declared = [
            EdiInstallment(number=str(number).zfill(3), date_due=due, amount=amount)
            for number, (due, amount) in enumerate(installments, 1)
        ]
        model = type(self.env["l10n_br_fiscal.document"])
        with mock.patch.object(model, "_edi_get_installments", return_value=declared):
            yield

    def _payables(self, partner=None):
        return self.env["account.move.line"].search(
            [
                ("partner_id", "=", (partner or self.supplier).id),
                ("account_id.account_type", "in", DUE_LINE_ACCOUNT_TYPES),
            ]
        )

    def _due_lines(self, move):
        return move.line_ids.filtered(
            lambda line: line.account_id.account_type in DUE_LINE_ACCOUNT_TYPES
        ).sorted("date_maturity")

    @staticmethod
    def _day(month, day):
        return date(2026, month, day)
