# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestAssessmentFromFiscalInvoice(AccountMoveBRCommon):
    """The assessment against invoices built by the BRAZILIAN engine.

    Every other compute test creates `account.tax` records by hand and posts a
    plain invoice on them, which proves the arithmetic but not the bridge: the
    taxes a real Brazilian invoice carries are chosen by the fiscal operation,
    the CFOP and the tax definitions, and they reach the accounting through
    `fiscal_tax_ids` -> `tax_ids`. If that mapping breaks, or if the invoice
    posts with no tax at all, every test here would still pass while the
    assessment silently reported zero.

    That is not hypothetical: on a demo database today the posted invoices
    carry no tax line at all, so the assessment shows nothing to assess.
    """

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        # Opt in to the fiscal tax definitions of the demo company: without
        # them the engine has nothing approved to apply and the invoice posts
        # with no tax, which is exactly the failure this test exists to catch.
        cls.configure_normal_company_taxes()
        cls.company = cls.company_data["company"]

        cls.invoice = cls.init_invoice(
            "out_invoice",
            products=[cls.product_a],
            invoice_date="2026-07-10",
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_lc_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_venda")],
            post=True,
        )

        # A creditable input: the tax leaves the cost of the goods and becomes
        # recoverable, which is what a manufacturer does with its raw material.
        cls.env.ref("l10n_br_fiscal.fo_compras").deductible_taxes = True
        cls.purchase = cls.init_invoice(
            "in_invoice",
            products=[cls.product_a],
            invoice_date="2026-07-05",
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_compras_compras")],
            document_serie="1",
            document_number="42",
            post=True,
        )

    def _assessment(self, group_xmlid):
        return self.env["l10n_br_tax.assessment"].create(
            {
                "company_id": self.company.id,
                "tax_group_id": self.env.ref(group_xmlid).id,
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
            }
        )

    def test_invoice_posts_with_brazilian_taxes(self):
        """Guard for the test below: the invoice must carry tax to begin with.

        Asserting the assessment alone would pass on an invoice with no tax by
        reading zero on both sides, so the fixture states its own premise.
        """
        self.assertEqual(self.invoice.state, "posted")
        line = self.invoice.invoice_line_ids[0]
        self.assertTrue(
            line.fiscal_tax_ids,
            "the fiscal engine applied no tax: the assessment below would be "
            "vacuously zero",
        )
        self.assertTrue(line.tax_ids, "the fiscal taxes did not reach account.tax")
        tax_lines = self.invoice.line_ids.filtered(lambda ml: ml.tax_line_id)
        self.assertTrue(tax_lines, "the posted invoice produced no tax journal item")

    def test_assessment_reads_the_icms_of_a_fiscal_invoice(self):
        """The ICMS the invoice booked is the ICMS the assessment reports."""
        icms_lines = self.invoice.line_ids.filtered(
            lambda ml: ml.tax_line_id
            and ml.tax_line_id.tax_group_id
            == self.env.ref("l10n_br_coa.tax_group_icms")
        )
        booked = sum(icms_lines.mapped("credit")) - sum(icms_lines.mapped("debit"))
        self.assertGreater(booked, 0.0, "the sale booked no ICMS to assess")

        assessment = self._assessment("l10n_br_coa.tax_group_icms")
        assessment.action_compute()

        self.assertAlmostEqual(assessment.debit_total, booked, places=2)
        debits = assessment.line_ids.filtered(
            lambda li: li.source == "computed" and li.kind == "debit"
        )
        self.assertTrue(debits, "the sale produced no debit line")
        # The period also carries the creditable purchase of the fixture, so
        # what is due is the offsetting of the two rather than the sale alone.
        # Asserting the sale amount as the amount payable would only hold while
        # the credit side was broken.
        self.assertAlmostEqual(
            assessment.balance,
            assessment.debit_total - assessment.credit_total,
            places=2,
        )

    def test_assessment_covers_the_four_consumption_taxes(self):
        """ICMS, IPI, PIS and COFINS each assess on their own group.

        The four are what the tax books need: ICMS and IPI feed block E of EFD
        ICMS/IPI, PIS and COFINS feed block M of EFD Contribuicoes. A group
        left out here is a block that serializes nothing.
        """
        for group_xmlid in (
            "l10n_br_coa.tax_group_icms",
            "l10n_br_coa.tax_group_ipi",
            "l10n_br_coa.tax_group_pis",
            "l10n_br_coa.tax_group_cofins",
        ):
            with self.subTest(group=group_xmlid):
                group = self.env.ref(group_xmlid)
                booked_lines = self.invoice.line_ids.filtered(
                    lambda ml, g=group: ml.tax_line_id
                    and ml.tax_line_id.tax_group_id == g
                )
                if not booked_lines:
                    self.skipTest("%s not applied by this operation" % group.name)
                booked = sum(booked_lines.mapped("credit")) - sum(
                    booked_lines.mapped("debit")
                )
                assessment = self._assessment(group_xmlid)
                assessment.action_compute()
                self.assertAlmostEqual(assessment.debit_total, booked, places=2)

    def test_creditable_purchase_becomes_credit_not_zero(self):
        """A creditable input has to show up as CREDIT in the assessment.

        This is the case that cancelled itself out. A deductible input posts a
        pair: the tax debits the recoverable account and its "Dedutivel"
        counterpart credits the cost by the same amount, so the tax leaves the
        cost of the goods. Both belong to the assessed group and both are of
        type purchase, so reading both sums a value and its negative and the
        credit vanishes, leaving an assessment that says a period full of
        creditable purchases generated no credit at all.

        Asserting on the total alone would not catch it either, since zero is a
        legitimate total for a period without purchases: the fixture posts a
        purchase with tax and the test states that premise first.
        """
        recoverable = self.purchase.line_ids.filtered(
            lambda ml: ml.tax_line_id
            and ml.tax_line_id.tax_group_id
            == self.env.ref("l10n_br_coa.tax_group_icms")
            and ml.debit
        )
        booked = sum(recoverable.mapped("debit")) - sum(recoverable.mapped("credit"))
        self.assertGreater(
            booked, 0.0, "the purchase booked no recoverable ICMS to assess"
        )

        assessment = self._assessment("l10n_br_coa.tax_group_icms")
        assessment.action_compute()

        self.assertAlmostEqual(assessment.credit_total, booked, places=2)
        credits = assessment.line_ids.filtered(
            lambda li: li.source == "computed" and li.kind == "credit"
        )
        self.assertTrue(
            credits, "the creditable purchase produced no credit line at all"
        )

    def test_deductible_counterpart_is_not_assessed_twice(self):
        """The counterpart tax is excluded, not merely netted.

        Keeping it in the set is what made the credit cancel out, so the guard
        belongs on the selection of taxes rather than on the arithmetic.
        """
        assessment = self._assessment("l10n_br_coa.tax_group_icms")
        counterparts = assessment._get_taxes().filtered(
            lambda tax: assessment._is_counterpart_tax(tax)
        )
        self.assertFalse(counterparts, "the counterpart tax is still being assessed")
