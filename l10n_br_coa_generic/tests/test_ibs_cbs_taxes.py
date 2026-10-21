# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_br_coa.tests.common import IbsCbsTaxesMixin


@tagged("post_install", "-at_install")
class TestIbsCbsTaxesGeneric(IbsCbsTaxesMixin, TransactionCase):
    """The taxes of the generic chart use its own accounts, by exact code.

    Non deductible IBS, CBS and IS go to "a Recolher" (2.1.7.1.14 to 16) and
    "a Compensar" (1.1.4.1.12 to 14). The deductible ones follow the ICMS:
    the sale goes to the revenue deduction ("s/ Vendas", 6.1.1.2.12 to 14) and
    the refund to the return account (6.1.1.2.32 to 34). On a purchase the
    credit goes to "s/ Vendas" too, and the refund to "a Recolher".
    """

    chart_template = "br_oca_generic"
    new_plan_account_codes = (
        "1.1.4.1.12",
        "1.1.4.1.13",
        "1.1.4.1.14",
        "2.1.7.1.14",
        "2.1.7.1.15",
        "2.1.7.1.16",
        "6.1.1.2.12",
        "6.1.1.2.13",
        "6.1.1.2.14",
    )
    expected_accounts = {
        "tax_template_out_ibs": ("2.1.7.1.14", "1.1.4.1.12"),
        "tax_template_in_ibs": ("1.1.4.1.12", "2.1.7.1.14"),
        "tax_template_out_cbs": ("2.1.7.1.15", "1.1.4.1.13"),
        "tax_template_in_cbs": ("1.1.4.1.13", "2.1.7.1.15"),
        "tax_template_out_ibs_deductible": ("6.1.1.2.12", "6.1.1.2.32"),
        "tax_template_in_ibs_deductible": ("6.1.1.2.12", "2.1.7.1.14"),
        "tax_template_out_cbs_deductible": ("6.1.1.2.13", "6.1.1.2.33"),
        "tax_template_in_cbs_deductible": ("6.1.1.2.13", "2.1.7.1.15"),
        "tax_template_out_is": ("2.1.7.1.16", "1.1.4.1.14"),
        "tax_template_in_is": ("1.1.4.1.14", "2.1.7.1.16"),
        "tax_template_out_is_deductible": ("6.1.1.2.14", "6.1.1.2.34"),
        "tax_template_in_is_deductible": ("6.1.1.2.14", "2.1.7.1.16"),
    }

    def test_no_account_with_a_review_suffix_beside_the_chart_ones(self):
        codes = [
            account.code
            for account in self.env["account.account"]
            .with_company(self.company)
            .search([("company_ids", "in", self.company.id)])
        ]
        for code in codes:
            if code.endswith((".GEN", ".BR")):
                self.assertNotIn(code.rsplit(".", 1)[0], codes, code)
