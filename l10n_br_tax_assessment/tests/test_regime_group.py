# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRegimeOfTheGroup(TransactionCase):
    """The PIS/COFINS regime of the tax group has a screen, and a group that
    does not say it follows the company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "Empresa do regime", "profit_calculation": "presumed"}
        )

    def _assessment(self, tax_domain, regime="not_applicable"):
        group = self.env["account.tax.group"].create(
            {
                "name": "%s (teste do regime)" % tax_domain,
                "fiscal_tax_group_id": self.env.ref(
                    "l10n_br_fiscal.tax_group_%s" % tax_domain
                ).id,
                "regime": regime,
            }
        )
        return self.env["l10n_br_tax.assessment"].create(
            {
                "company_id": self.company.id,
                "tax_group_id": group.id,
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
            }
        )

    def test_a_company_of_the_presumed_profit_is_cumulative(self):
        for domain in ("pis", "cofins"):
            self.assertEqual(self._assessment(domain).regime, "cumulative", domain)

    def test_a_company_of_the_arbitrary_profit_is_cumulative(self):
        self.company.profit_calculation = "arbitrary"
        self.assertEqual(self._assessment("pis").regime, "cumulative")

    def test_a_company_of_the_real_profit_is_non_cumulative(self):
        self.company.profit_calculation = "real"
        for domain in ("pis", "cofins"):
            self.assertEqual(self._assessment(domain).regime, "non_cumulative", domain)

    def test_the_icms_and_the_ipi_have_no_regime(self):
        self.company.profit_calculation = "real"
        for domain in ("icms", "ipi"):
            self.assertEqual(self._assessment(domain).regime, "not_applicable", domain)

    def test_the_regime_of_the_group_wins(self):
        assessment = self._assessment("pis", regime="non_cumulative")
        self.assertEqual(assessment.regime, "non_cumulative")
        assessment.tax_group_id.regime = "cumulative"
        self.assertEqual(assessment.regime, "cumulative")

    def test_the_tax_group_screens_of_the_core_have_the_regime(self):
        """The form and the list of the action of the core carry the regime, and
        there is no second action for the same model."""
        model = self.env["account.tax.group"]
        self.assertIn('name="regime"', model.get_view(view_type="form")["arch"])
        action = self.env.ref("account.action_tax_group")
        tree = model.get_view(view_id=action.view_id.id, view_type="tree")
        self.assertIn('name="regime"', tree["arch"])
        actions = self.env["ir.actions.act_window"].search(
            [("res_model", "=", "account.tax.group")]
        )
        self.assertEqual(actions, action)

    def test_the_accounting_manager_reaches_the_tax_groups_without_debug(self):
        """The menu of the core needs the developer mode; ours opens the same
        action without it."""
        user = self.env["res.users"].create(
            {
                "name": "Accounting manager",
                "login": "accounting_manager_tax_group",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("account.group_account_user").id,
                            self.env.ref("account.group_account_manager").id,
                        ],
                    )
                ],
            }
        )
        menu = self.env.ref("l10n_br_tax_assessment.menu_tax_group_regime")
        self.assertEqual(menu.action, self.env.ref("account.action_tax_group"))
        visible = self.env["ir.ui.menu"].with_user(user)._visible_menu_ids(debug=False)
        self.assertIn(menu.id, visible)
        self.assertNotIn(self.env.ref("account.menu_action_tax_group").id, visible)
