# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestIcmsFcpDeductible(AccountMoveBRCommon):
    """With deductible taxes the ICMS FCP must not raise the receivable."""

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        company = cls.company_data["company"]
        cls.partner_a.state_id = company.state_id
        cls.product_a.ncm_id.tax_ipi_id = cls.env.ref("l10n_br_fiscal.tax_ipi_nt")
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.operation_line = cls.env.ref("l10n_br_fiscal.fo_venda_venda")
        for group, tax in (("icms", "tax_icms_18"), ("icmsfcp", "tax_icmsfcp_2")):
            cls.env["l10n_br_fiscal.tax.definition"].create(
                {
                    "company_id": company.id,
                    "tax_group_id": cls.env.ref(f"l10n_br_fiscal.tax_group_{group}").id,
                    "is_taxed": True,
                    "is_debit_credit": True,
                    "custom_tax": True,
                    "tax_id": cls.env.ref(f"l10n_br_fiscal.{tax}").id,
                    "cst_id": cls.env.ref("l10n_br_fiscal.cst_icms_00").id,
                    "state": "approved",
                    "fiscal_operation_line_id": cls.operation_line.id,
                }
            )
        cls.operation.with_company(company).deductible_taxes = True
        cls.document_serie = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "1",
                "name": "Serie 1",
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "company_id": company.id,
            }
        )

    def test_receivable_equals_invoice_total(self):
        move = self.init_invoice(
            "out_invoice",
            products=[self.product_a],
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=self.document_serie,
            fiscal_operation=self.operation,
            fiscal_operation_lines=[self.operation_line],
        )
        move.action_post()
        line = move.invoice_line_ids
        self.assertAlmostEqual(line.icmsfcp_value, 20.0, places=2)
        self.assertAlmostEqual(move.amount_residual, move.amount_total, places=2)
        self.assertAlmostEqual(move.amount_total, line.fiscal_amount_total, places=2)
