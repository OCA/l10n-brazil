# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class L10nBrCoaPoppi(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.l10n_br_coa_poppi = cls.env.ref(
            "l10n_br_coa_poppi.l10n_br_coa_poppi_chart_template"
        )
        cls.l10n_br_company = cls.env["res.company"].create(
            {
                "name": "Empresa Teste do Plano de Contas",
                "currency_id": cls.env.ref("base.BRL").id,
                "country_id": cls.env.ref("base.br").id,
            }
        )
        cls.l10n_br_coa_poppi.try_loading(company=cls.l10n_br_company)

    def test_l10n_br_coa_poppi(self):
        """Test installing the chart of accounts template in a new company"""
        self.assertEqual(self.l10n_br_coa_poppi, self.l10n_br_company.chart_template_id)
        self.assertTrue(self.l10n_br_company.anglo_saxon_accounting)
        self.assertEqual(self.l10n_br_company.cash_account_code_prefix, "111.01.")
        self.assertEqual(self.l10n_br_company.bank_account_code_prefix, "111.02.")
        partner = (
            self.env["res.partner"]
            .with_company(self.l10n_br_company)
            .create({"name": "Cliente Teste"})
        )
        self.assertEqual(partner.property_account_receivable_id.code, "112.01.01")
        self.assertEqual(partner.property_account_payable_id.code, "211.01.01")

    def test_tax_group_accounts(self):
        mappings = {
            "pis": ("211.05.23", "112.07.06"),
            "cofins": ("112.07.08", "112.07.08"),
            "issqn": ("211.05.06", "211.05.06"),
            "ipi": ("211.05.07", "112.07.02"),
        }
        for group, (code, refund_code) in mappings.items():
            taxes = self.env["account.tax"].search(
                [
                    ("company_id", "=", self.l10n_br_company.id),
                    (
                        "tax_group_id",
                        "=",
                        self.env.ref(f"l10n_br_coa.tax_group_{group}").id,
                    ),
                ]
            )
            self.assertTrue(taxes)
            for tax in taxes:
                expected = (code, refund_code)
                if tax.deductible or (
                    tax.withholdable and tax.type_tax_use != "purchase"
                ):
                    expected = (False, False)
                elif tax.type_tax_use == "purchase" and not tax.withholdable:
                    expected = (refund_code, code)
                for lines, account_code in zip(
                    (tax.invoice_repartition_line_ids, tax.refund_repartition_line_ids),
                    expected,
                    strict=True,
                ):
                    tax_lines = lines.filtered(
                        lambda line: line.repartition_type == "tax"
                    )
                    self.assertTrue(tax_lines)
                    for line in tax_lines:
                        self.assertEqual(line.account_id.code, account_code)
