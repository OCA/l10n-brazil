# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date
from unittest.mock import patch

from odoo.tests.common import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestImportedDueDate(AccountMoveBRCommon):
    chart_template = "generic_coa"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["account.chart.template"].load_fiscal_taxes(
            companies=[cls.company_data["company"]]
        )
        cls.configure_normal_company_taxes()

        cls.move = cls.init_invoice(
            "in_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[
                cls.env.ref("l10n_br_fiscal.fo_compras_compras_comercializacao")
            ],
            document_serie="1",
            document_number="4952",
        )
        cls.move.fiscal_document_id.sudo().imported_document = True

    def _terms_with(self, installments):
        document = self.move.fiscal_document_id
        with patch.object(
            type(document),
            "_get_imported_installments",
            lambda doc: installments,
        ):
            self.move._compute_needed_terms()
        return self.move.needed_terms

    def test_the_due_dates_come_from_the_file(self):
        """Without this the imported bill is due on the day it was imported."""
        terms = self._terms_with(
            [(date(2026, 9, 4), 300.0), (date(2026, 10, 4), 700.0)]
        )

        self.assertEqual(
            sorted(key["date_maturity"] for key in terms),
            [date(2026, 9, 4), date(2026, 10, 4)],
        )

    def test_the_installments_add_up_to_the_document_total(self):
        """The move has to balance even when the file does not add up.

        The weights come from the file, the total comes from the document, so
        the terms always close on amount_total_signed.
        """
        terms = self._terms_with([(date(2026, 9, 4), 1.0), (date(2026, 10, 4), 2.0)])

        self.assertAlmostEqual(
            sum(values["balance"] for values in terms.values()),
            self.move.amount_total_signed,
            places=2,
        )
        by_date = {key["date_maturity"]: values for key, values in terms.items()}
        one_third = self.move.amount_total_signed / 3
        self.assertAlmostEqual(
            by_date[date(2026, 9, 4)]["balance"], one_third, places=2
        )

    def test_installments_on_the_same_date_are_merged(self):
        terms = self._terms_with([(date(2026, 9, 4), 400.0), (date(2026, 9, 4), 600.0)])

        self.assertEqual(len(terms), 1)
        self.assertAlmostEqual(
            next(iter(terms.values()))["balance"],
            self.move.amount_total_signed,
            places=2,
        )

    def test_a_file_without_installments_keeps_the_single_term(self):
        terms = self._terms_with([])

        self.assertEqual(len(terms), 1)
        self.assertEqual(
            next(iter(terms))["date_maturity"],
            self.move.invoice_date_due,
        )
