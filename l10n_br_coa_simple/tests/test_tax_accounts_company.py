# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_br_coa.models.template_br_oca import DEFAULT_TAX_ACCOUNTS

SIMPLE_ICMS_CODE = "2.1.4.02.06"  # "ICMS", an account of the simple chart


@tagged("post_install", "-at_install")
class TestTaxAccountsCompany(TransactionCase):
    """The default tax accounts are the ones of the chart, in the new company.

    The code of an account belongs to a company. The search for the account of
    the chart ran in the company of the user instead of the one being loaded,
    so the account was never found and a copy with the review suffix (`.GEN`,
    `.BR`) was created beside it.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The user company is NOT the one being loaded: this is what makes the
        # search look at the wrong company.
        cls.chart = cls.env["account.chart.template"]
        vals = {
            "name": "Empresa Plano Simples",
            "country_id": cls.env.ref("base.br").id,
            "currency_id": cls.env.ref("base.BRL").id,
        }
        if "tax_framework" in cls.env["res.company"]._fields:
            vals["tax_framework"] = "1"  # Simples Nacional: ITG codes
        cls.company = cls.env["res.company"].create(vals)
        cls.env.user.company_ids |= cls.company

    def _codes(self):
        accounts = (
            self.env["account.account"]
            .with_company(self.company)
            .search([("company_ids", "in", self.company.id)])
        )
        return accounts.mapped("code")

    def _icms_codes(self):
        tax = self.env.ref(
            f"account.{self.company.id}_tax_template_out_icms",
            raise_if_not_found=False,
        ) or self.env.ref(f"l10n_br_coa.{self.company.id}_tax_template_out_icms")
        codes = []
        for lines in (
            tax.invoice_repartition_line_ids,
            tax.refund_repartition_line_ids,
        ):
            line = lines.filtered(lambda line: line.repartition_type == "tax")
            codes.append(line.account_id.with_company(self.company).code)
        return tuple(codes)

    def test_tax_uses_the_chart_account(self):
        """A default tax account that the chart has is reused, with no suffix."""
        code_cfc, _code_itg, name, acc_type = DEFAULT_TAX_ACCOUNTS["tax_icms_payable"]
        patched = (code_cfc, SIMPLE_ICMS_CODE, name, acc_type)
        with patch.dict(DEFAULT_TAX_ACCOUNTS, {"tax_icms_payable": patched}):
            self.chart.try_loading("br_oca_simple", self.company, install_demo=False)
        self.assertEqual(self.company.chart_template, "br_oca_simple")
        self.assertEqual(self._icms_codes()[0], SIMPLE_ICMS_CODE)
        codes = self._codes()
        self.assertEqual(codes.count(SIMPLE_ICMS_CODE), 1)
        self.assertNotIn(f"{SIMPLE_ICMS_CODE}.GEN", codes)
        self.assertNotIn(f"{SIMPLE_ICMS_CODE}.BR", codes)

    def test_no_second_set_of_accounts(self):
        """The accounts created by the load are reused, not copied."""
        self.chart.try_loading("br_oca_simple", self.company, install_demo=False)
        codes = self._codes()
        self.assertFalse(
            [code for code in codes if code.endswith(".BR")],
            "the fiscal taxes must reuse the accounts the chart load created",
        )
        before = sorted(codes)
        icms = self._icms_codes()
        self.chart._populate_default_br_tax_accounts(self.company, flavor="itg")
        self.assertEqual(sorted(self._codes()), before)
        self.assertEqual(self._icms_codes(), icms)
