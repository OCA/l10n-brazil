# Copyright 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestIcmsStDeductible(AccountMoveBRCommon):
    """The ICMS ST of a sale must not be added twice to the receivable.

    With deductible taxes the product line takes the full document total, ST
    included, and the deductible account tax gives each tax back with a
    negative factor. Without the deductible ICMS ST the ST tax line adds the
    ST once more and the title is bigger than the invoice total.

    Sale of 1.000,00 with own ICMS of 20% (200,00) and ICMS ST of 20% with an
    MVA of 50%: ST base 1.500,00, ST 300,00 - 200,00 = 100,00. Invoice total
    and receivable: 1.100,00.
    """

    chart_template = "generic_coa"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The complex_tax of the core fixture is not a fiscal tax and falls in
        # a fiscal tax group, unbalancing the entry (see test_ibs_cbs_deductible).
        cls.env["account.tax"].with_context(active_test=False).search(
            [("name", "like", "complex_tax")]
        ).unlink()
        cls.company = cls.company_data["company"]
        cls.env["account.chart.template"].load_fiscal_taxes(companies=[cls.company])
        cls.configure_normal_company_taxes()
        icmsst_20_mva_50 = cls.env["l10n_br_fiscal.tax"].create(
            {
                "name": "ICMS ST 20% MVA 50%",
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_icmsst").id,
                "tax_base_type": "percent",
                "percent_amount": 20.0,
                "percent_reduction": 0.0,
                "percent_debit_credit": 0.0,
                "value_amount": 0.0,
                "icmsst_value": 0.0,
                "icmsst_base_type": "4",
                "icmsst_mva_percent": 50.0,
                "cst_in_id": cls.env.ref("l10n_br_fiscal.cst_icms_10").id,
                "cst_out_id": cls.env.ref("l10n_br_fiscal.cst_icms_10").id,
            }
        )
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.operation_line = cls.env.ref("l10n_br_fiscal.fo_venda_venda")
        tax_def_model = cls.env["l10n_br_fiscal.tax.definition"]
        # IPI out of the way (the IPI of the NCM would enter the ST base):
        # only ICMS and ST on the line.
        cls.product_a.ncm_id.tax_ipi_id = cls.env.ref("l10n_br_fiscal.tax_ipi_nt")
        for group, tax, cst in (
            ("icms", cls.env.ref("l10n_br_fiscal.tax_icms_20"), "cst_icms_10"),
            ("icmsst", icmsst_20_mva_50, "cst_icms_10"),
        ):
            tax_def_model.create(
                {
                    "company_id": cls.company.id,
                    "tax_group_id": cls.env.ref(f"l10n_br_fiscal.tax_group_{group}").id,
                    "is_taxed": True,
                    "is_debit_credit": True,
                    "custom_tax": True,
                    "tax_id": tax.id,
                    "cst_id": cls.env.ref(f"l10n_br_fiscal.{cst}").id,
                    "state": "approved",
                    "fiscal_operation_line_id": cls.operation_line.id,
                }
            )
        cls.operation.with_company(cls.company).deductible_taxes = True

    def _sale_move(self):
        return self.init_invoice(
            "out_invoice",
            products=[self.product_a],
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=self.empresa_lc_document_55_serie_1,
            fiscal_operation=self.operation,
            fiscal_operation_lines=[self.operation_line],
        )

    def test_receivable_equals_invoice_total(self):
        """Sale of 1.000,00 with 100,00 of ICMS ST: the title is 1.100,00."""
        move = self._sale_move()
        move.action_post()
        self.assertAlmostEqual(move.amount_total, 1100.0, places=2)
        self.assertAlmostEqual(move.amount_residual, 1100.0, places=2)
