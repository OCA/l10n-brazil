# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""The classification of the shipped charts has to stay complete.

The reports select accounts by classification, so an account that loses its tag
does not raise: it silently drops out of the statement, and the statement stops
tying. These tests are what turns that into a failure at build time.
"""
from odoo.tests import TransactionCase, tagged

CASH_FLOW_TAGS = (
    "account_tag_cash_and_equivalents",
    "account_tag_cash_flow_operating",
    "account_tag_cash_flow_investing",
    "account_tag_cash_flow_financing",
    "account_tag_cash_flow_non_cash",
    "account_tag_cash_flow_result_adjustment",
)

DVA_TAGS = (
    "account_tag_dva_inputs",
    "account_tag_dva_personnel",
    "account_tag_dva_taxes",
    "account_tag_dva_third_party_capital",
    "account_tag_dva_own_capital",
    "account_tag_dva_transfer",
)


@tagged("post_install", "-at_install")
class TestAccountClassification(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Only the accounts THIS localisation ships. Filtering by the module
        # that declares them is what keeps a chart of another localisation,
        # installed side by side, out of the assertions: it has no reason to
        # carry Brazilian classification, and the test would fail on it.
        data = cls.env["ir.model.data"].search(
            [
                ("model", "=", "account.account.template"),
                ("module", "=like", "l10n_br_coa%"),
            ]
        )
        cls.templates = (
            cls.env["account.account.template"].browse(data.mapped("res_id")).exists()
        )

    def setUp(self):
        super().setUp()
        if not self.templates:
            self.skipTest("nenhum plano de contas brasileiro instalado")

    def _tag(self, name):
        return self.env.ref("l10n_br_coa.%s" % name)

    def _tagged_with(self, names):
        ids = [self._tag(name).id for name in names]
        return self.templates.filtered(lambda t: set(t.tag_ids.ids) & set(ids))

    def test_every_account_carries_a_report_line(self):
        """No account is left out of the balance sheet and income statement."""
        untagged = self.templates.filtered(lambda t: not t.tag_ids)
        self.assertFalse(
            untagged,
            "contas sem classificação: %s"
            % ", ".join(f"{t.code} {t.name}" for t in untagged[:10]),
        )

    def test_balance_accounts_declare_one_cash_flow_activity(self):
        """Every balance account says which activity it belongs to.

        The cash flow statement is a reconciliation: an account with no
        activity simply vanishes from it, and the movement it carried shows up
        as an unexplained difference against the cash account.
        """
        result = self._tag("account_tag_result")
        balance = self.templates.filtered(lambda t: result not in t.tag_ids)
        cash_flow_ids = [self._tag(name).id for name in CASH_FLOW_TAGS]
        for account in balance:
            declared = set(account.tag_ids.ids) & set(cash_flow_ids)
            self.assertEqual(
                len(declared),
                1,
                "a conta {} {} declara {} atividades de fluxo de caixa, e tem "
                "que declarar exatamente uma".format(
                    account.code, account.name, len(declared)
                ),
            )

    def test_a_result_account_never_declares_an_activity(self):
        """Result accounts enter the cash flow through the result, only once.

        They reach the statement as the first line, the result of the year.
        Classifying them by activity as well would count the same amount twice,
        and the reconciliation with cash would break by exactly that amount.
        """
        result = self._tag("account_tag_result")
        cash_flow_ids = [self._tag(name).id for name in CASH_FLOW_TAGS]
        both = self.templates.filtered(
            lambda t: result in t.tag_ids and set(t.tag_ids.ids) & set(cash_flow_ids)
        )
        self.assertFalse(
            both,
            "contas de resultado com atividade de fluxo de caixa: {}".format(
                ", ".join(f"{t.code} {t.name}" for t in both[:10])
            ),
        )

    def test_expense_accounts_declare_how_they_distribute_value(self):
        """Every cost and expense says where it lands on the value added.

        The value added statement has to tie: what is distributed equals what
        there is to distribute. An expense with no destination breaks the
        equality the CPC 09 requires.
        """
        result = self._tag("account_tag_result")
        revenue_ids = [
            self._tag(name).id
            for name in (
                "account_tag_revenue",
                "account_tag_other_operating_results",
            )
        ]
        dva_ids = [self._tag(name).id for name in DVA_TAGS]
        expenses = self.templates.filtered(
            lambda t: result in t.tag_ids
            and not (set(t.tag_ids.ids) & set(revenue_ids))
        )
        for account in expenses:
            self.assertTrue(
                set(account.tag_ids.ids) & set(dva_ids),
                "a conta de resultado {} {} não diz como distribui o valor "
                "adicionado".format(account.code, account.name),
            )
