# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""The classification of the shipped charts has to stay complete.

The reports select accounts by classification, so an account that loses its tag
does not raise: it silently drops out of the statement, and the statement stops
tying. These tests are what turns that into a failure at build time.

Odoo 18 has no `account.account.template`: the assertions run on the accounts
the chart load created, found through the `ir.model.data` the load writes
(`{company_id}_{csv key}`, module `account`). A chart flavor that is not
installed ships no accounts here and the class skips.
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

CHART_MODULES = ("l10n_br_coa_generic", "l10n_br_coa_simple")


@tagged("post_install", "-at_install")
class TestAccountClassification(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        installed = set(
            cls.env["ir.module.module"]
            .search([("state", "=", "installed")])
            .mapped("name")
        )
        ChartTemplate = cls.env["account.chart.template"]
        # Only the accounts THIS localisation ships: the csv keys of the
        # installed chart flavors, resolved through the ir.model.data the
        # chart load created. A chart of another localisation installed side
        # by side has no reason to carry Brazilian classification, and the
        # test would fail on it.
        keys = []
        for template_code, mapping in ChartTemplate._get_chart_template_mapping(
            get_all=True
        ).items():
            if mapping.get("module") not in CHART_MODULES:
                continue
            if not {mapping["module"], "l10n_br_coa"} <= installed:
                continue
            account_data = ChartTemplate._parse_csv(template_code, "account.account")
            keys.extend(account_data)
        cls.templates = cls.env["account.account"]
        if not keys:
            return
        # accounts are company records: every company that loaded the chart
        # has its own `{company_id}_{key}` mapping
        data = cls.env["ir.model.data"].search(
            [
                ("model", "=", "account.account"),
                (
                    "name",
                    "in",
                    [
                        f"{c.id}_{k}"
                        for c in cls.env["res.company"].search([])
                        for k in keys
                    ],
                ),
            ]
        )
        cls.templates = (
            cls.env["account.account"].browse(data.mapped("res_id")).exists()
        )

    def setUp(self):
        super().setUp()
        if not self.templates:
            self.skipTest("nenhum plano de contas brasileiro instalado")

    def _tag(self, name):
        return self.env.ref("l10n_br_coa." + name)

    def _tagged_with(self, names):
        ids = [self._tag(name).id for name in names]
        return self.templates.filtered(lambda t: set(t.tag_ids.ids) & set(ids))

    def test_every_account_carries_a_report_line(self):
        """No account is left out of the balance sheet and income statement."""
        untagged = self.templates.filtered(lambda t: not t.tag_ids)
        self.assertFalse(
            untagged,
            "contas sem classificação: "
            + ", ".join(f"{t.code} {t.name}" for t in untagged[:10]),
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
                f"a conta {account.code} {account.name} declara "
                f"{len(declared)} atividades de fluxo de caixa, e tem "
                "que declarar exatamente uma",
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
            "contas de resultado com atividade de fluxo de caixa: "
            + ", ".join(f"{t.code} {t.name}" for t in both[:10]),
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
                f"a conta de resultado {account.code} {account.name} "
                "não diz como distribui o valor adicionado",
            )

    def test_a_revenue_never_lands_on_the_distribution_side(self):
        """Revenue forms the value added, it is never distributed.

        In the CPC 09 model a revenue enters the value added either as sales
        (line 1) or as value added received in transfer (line 6), where the
        financial revenues go, exchange gains included (6.2). The distribution
        (line 8) only holds what the entity pays out: personnel, taxes, the
        remuneration of third party and own capital. A revenue tagged there
        would be subtracted from the total it should have increased.

        Deductions of revenue are the exception: the taxes on sales are typed
        as revenue and are distributed to the government (8.2).
        """
        deduction = self._tag("account_tag_revenue_deduction")
        distribution_ids = [
            self._tag(name).id
            for name in (
                "account_tag_dva_personnel",
                "account_tag_dva_taxes",
                "account_tag_dva_third_party_capital",
                "account_tag_dva_own_capital",
            )
        ]
        wrong = self.templates.filtered(
            lambda t: t.account_type in ("income", "income_other")
            and deduction not in t.tag_ids
            and set(t.tag_ids.ids) & set(distribution_ids)
        )
        self.assertFalse(
            wrong,
            "receitas classificadas na distribuição do valor adicionado: "
            + ", ".join(f"{t.code} {t.name}" for t in wrong[:10]),
        )
