# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import importlib.util

from odoo import Command
from odoo.modules.module import get_module_path

LOGGER_NAME = "l10n_br_coa_post_migration_18_0_3_4_0"
NEW_GROUP = "tax_group_is"
NEW_TAXES = [
    "tax_template_out_ibs_deductible",
    "tax_template_in_ibs_deductible",
    "tax_template_out_cbs_deductible",
    "tax_template_in_cbs_deductible",
    "tax_template_out_is",
    "tax_template_in_is",
    "tax_template_out_is_deductible",
    "tax_template_in_is_deductible",
]
PLAIN_TAXES = [
    "tax_template_out_ibs",
    "tax_template_in_ibs",
    "tax_template_out_cbs",
    "tax_template_in_cbs",
]
ALL_TAXES = PLAIN_TAXES + NEW_TAXES


def load_migration():
    """Import the migration script of `l10n_br_coa` 18.0.3.4.0.

    The folder of a migration is named after the version (`18.0.3.4.0`) and
    the file `post-migration.py` has a dash: neither is a valid module name,
    so a plain `import` cannot reach it and the script is loaded by path. It
    is the same file Odoo runs on `-u`.
    """
    path = get_module_path("l10n_br_coa")
    spec = importlib.util.spec_from_file_location(
        LOGGER_NAME,
        f"{path}/migrations/18.0.3.4.0/post-migration.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IbsCbsTaxesMixin:
    """IBS, CBS and IS come with their deductible taxes and the IS group.

    An operation that uses deductible taxes gives the tax back with a
    deductible account tax. Without the IBS and CBS ones the amount is added
    to the receivable a second time.

    Mixed in a `TransactionCase` by the module that owns each chart, so every
    chart is tested with its own accounts:

    * `chart_template`: the chart loaded in a new company;
    * `tax_framework`: the regime of the company (decides the account codes);
    * `expected_accounts`: tax key -> (invoice account, refund account), by
      exact code; `None` where the chart has no account of its own;
    * `new_plan_account_codes`: accounts that this version added to the chart.
    """

    # Odoo collects only the test methods defined in the class itself, unless
    # the class asks for the inherited ones: the tests live in this mixin.
    allow_inherited_tests_method = True
    chart_template = None
    tax_framework = None
    expected_accounts = None
    new_plan_account_codes = ()

    @classmethod
    def _create_company(cls, name, **vals):
        vals = {
            "name": name,
            "country_id": cls.env.ref("base.br").id,
            "currency_id": cls.env.ref("base.BRL").id,
            **vals,
        }
        if cls.tax_framework and "tax_framework" in cls.env["res.company"]._fields:
            vals["tax_framework"] = cls.tax_framework
        company = cls.env["res.company"].create(vals)
        # The company of the user is NOT the one being loaded: this is how a
        # real load happens (a new company created from the user's session).
        cls.env.user.company_ids |= company
        cls.env["account.chart.template"].try_loading(
            cls.chart_template, company, install_demo=False
        )
        return company

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls._create_company(f"Empresa IBS CBS {cls.chart_template}")
        cls.chart = cls.env["account.chart.template"]

    def _tax(self, key, company=None):
        company = company or self.company
        for module in ("account", "l10n_br_coa"):
            tax = self.env.ref(f"{module}.{company.id}_{key}", raise_if_not_found=False)
            if tax:
                return tax
        return self.env["account.tax"]

    def _tax_line(self, tax, refund=False):
        lines = (
            tax.refund_repartition_line_ids
            if refund
            else tax.invoice_repartition_line_ids
        )
        return lines.filtered(lambda line: line.repartition_type == "tax")

    def _account_codes(self, tax, company=None):
        company = company or self.company
        return tuple(
            self._tax_line(tax, refund=refund).account_id.with_company(company).code
            for refund in (False, True)
        )

    def _snapshot(self, company=None):
        """Taxes of the company with their accounts, and its account codes."""
        company = company or self.company
        taxes = self.env["account.tax"].search([("company_id", "=", company.id)])
        accounts = (
            self.env["account.account"]
            .with_company(company)
            .search([("company_ids", "in", company.id)])
        )
        return {
            "taxes": sorted(
                (
                    tax.name,
                    tax.type_tax_use,
                    tax.deductible,
                    *self._account_codes(tax, company),
                )
                for tax in taxes
            ),
            "accounts": sorted((account.code, account.name) for account in accounts),
        }

    def _assert_taxes_loaded(self):
        for key in ALL_TAXES:
            tax = self._tax(key)
            self.assertTrue(tax, f"{key} was not loaded")
            if key in NEW_TAXES:
                deductible = "deductible" in key
                self.assertEqual(tax.deductible, deductible, key)
                factor = -100 if deductible else 100
                self.assertEqual(self._tax_line(tax).factor_percent, factor, key)
            self.assertTrue(self._tax_line(tax).account_id, f"{key} has no account")
            if self.expected_accounts:
                self.assertEqual(
                    self._account_codes(tax), self.expected_accounts[key], key
                )
        self.assertTrue(self._tax(NEW_GROUP), "the IS tax group was not loaded")

    def _remove_new_taxes(self):
        """Leave the company as a database loaded before this version."""
        for key in NEW_TAXES:
            self._tax(key).unlink()
        self._tax(NEW_GROUP).unlink()
        self.assertFalse(self._tax(NEW_TAXES[0]))
        self.assertFalse(self._tax(NEW_GROUP))

    def _remove_new_plan_accounts(self):
        """Also remove the chart accounts this version added."""
        for key in PLAIN_TAXES:
            tax = self._tax(key)
            for refund in (False, True):
                self._tax_line(tax, refund=refund).account_id = False
        accounts = (
            self.env["account.account"]
            .with_company(self.company)
            .search(
                [
                    ("company_ids", "in", self.company.id),
                    ("code", "in", list(self.new_plan_account_codes)),
                ]
            )
        )
        self.assertEqual(len(accounts), len(self.new_plan_account_codes))
        accounts.unlink()

    def _migrate(self):
        # `migrate_companies` is the body of the `migrate` entry point: the
        # openupgrade decorator logs an ERROR when it is not called by Odoo
        # (it inspects the caller frame), which fails the log check of the CI.
        load_migration().migrate_companies(self.env)
        self.env.invalidate_all()

    def _custom_account(self, code, name):
        return (
            self.env["account.account"]
            .with_company(self.company)
            .create(
                {
                    "name": name,
                    "code": code,
                    "account_type": "liability_current",
                    "company_ids": [Command.link(self.company.id)],
                }
            )
        )

    # Tests

    def test_loaded_chart_has_the_new_taxes(self):
        self._assert_taxes_loaded()

    def test_migration_adds_the_missing_taxes(self):
        """A database loaded before this version gets the taxes."""
        self._remove_new_taxes()
        other = self._tax("tax_template_out_icms")
        other_codes = self._account_codes(other)
        # An account the migration must not rewrite.
        custom = self._custom_account("9.9.9.99", "Conta do cliente")
        self._tax_line(other).account_id = custom

        self._migrate()

        self._assert_taxes_loaded()
        self.assertEqual(
            self._tax_line(other).account_id,
            custom,
            "the migration rewrote the accounts of a tax that already existed",
        )
        self.assertNotEqual(custom.with_company(self.company).code, other_codes[0])

    def test_migration_gives_accounts_to_the_plain_ibs_and_cbs_taxes(self):
        """18.0 shipped the plain IBS and CBS taxes with no account."""
        empty = self._tax("tax_template_out_ibs")
        for refund in (False, True):
            self._tax_line(empty, refund=refund).account_id = False
        # A plain tax whose account somebody chose is left alone.
        custom_tax = self._tax("tax_template_out_cbs")
        custom = self._custom_account("9.9.9.98", "Conta escolhida")
        self._tax_line(custom_tax).account_id = custom

        self._migrate()

        self.assertTrue(self._tax_line(empty).account_id)
        if self.expected_accounts:
            self.assertEqual(
                self._account_codes(empty),
                self.expected_accounts["tax_template_out_ibs"],
            )
        self.assertEqual(self._tax_line(custom_tax).account_id, custom)

    def test_migration_is_idempotent(self):
        """Running it twice changes nothing, taxes and accounts included."""
        self._remove_new_taxes()
        self._migrate()
        first = self._snapshot()
        self._migrate()
        self.assertEqual(self._snapshot(), first)
        # On a company that already has everything it is a no-op as well.
        self._assert_taxes_loaded()

    def test_migration_keeps_the_tax_made_by_hand(self):
        """The deductible tax somebody created is not applied twice."""
        key = "tax_template_out_ibs_deductible"
        generated = self._tax(key)
        name = generated.name
        group = generated.tax_group_id
        generated.unlink()
        by_hand = self.env["account.tax"].create(
            {
                "name": name,
                "company_id": self.company.id,
                "tax_group_id": group.id,
                "type_tax_use": "sale",
                "deductible": True,
                "amount": 0.0,
            }
        )

        # The tax by hand has no account and no negative factor: it is kept
        # and the log says so.
        with self.assertLogs(LOGGER_NAME, level="WARNING"):
            self._migrate()

        taxes = self.env["account.tax"].search(
            [("company_id", "=", self.company.id), ("name", "=", name)]
        )
        self.assertEqual(taxes, by_hand)
        self.assertEqual(self._tax(key), by_hand)
        xmlid = by_hand.get_external_id()[by_hand.id]
        self.assertEqual(xmlid, f"account.{self.company.id}_{key}")

    def test_migration_finds_the_tax_by_what_it_does(self):
        """The workaround tax is found whatever its name."""
        key = "tax_template_out_ibs_deductible"
        generated = self._tax(key)
        group = generated.tax_group_id
        generated.unlink()
        by_hand = self.env["account.tax"].create(
            {
                "name": "IBS Dedutível",
                "company_id": self.company.id,
                "tax_group_id": group.id,
                "type_tax_use": "sale",
                "deductible": True,
                "amount": 0.0,
            }
        )

        # The tax by hand has no account and no negative factor: it is kept
        # and the log says so.
        with self.assertLogs(LOGGER_NAME, level="WARNING"):
            self._migrate()

        self.assertEqual(self._tax(key), by_hand)
        deductible_sale = self.env["account.tax"].search(
            [
                ("company_id", "=", self.company.id),
                ("tax_group_id", "=", group.id),
                ("type_tax_use", "=", "sale"),
                ("deductible", "=", True),
            ]
        )
        self.assertEqual(deductible_sale, by_hand, "a second tax was created")
        self.assertFalse(
            self.env["account.tax"].search_count(
                [
                    ("company_id", "=", self.company.id),
                    ("name", "=", "IBS Saída Dedutível"),
                ]
            )
        )

    def _remove_deductible_sale_tax(self):
        """Remove the chart IBS deductible sale tax; return its group."""
        generated = self._tax("tax_template_out_ibs_deductible")
        group = generated.tax_group_id
        generated.unlink()
        return group

    def _tax_by_hand(self, group, name, **vals):
        return self.env["account.tax"].create(
            {
                "name": name,
                "company_id": self.company.id,
                "tax_group_id": group.id,
                "type_tax_use": "sale",
                "deductible": True,
                "amount": 0.0,
                **vals,
            }
        )

    def _deductible_sale_taxes(self, group):
        return (
            self.env["account.tax"]
            .with_context(active_test=False)
            .search(
                [
                    ("company_id", "=", self.company.id),
                    ("tax_group_id", "=", group.id),
                    ("type_tax_use", "=", "sale"),
                    ("deductible", "=", True),
                ]
            )
        )

    def test_migration_keeps_the_tax_with_an_exported_xmlid(self):
        """An xmlid that is not the chart one does not hide the tax by hand.

        Exporting records from the screen gives them an `__export__` xmlid.
        """
        key = "tax_template_out_ibs_deductible"
        group = self._remove_deductible_sale_tax()
        by_hand = self._tax_by_hand(group, "IBS Dedutível")
        by_hand.export_data(["id", "name"])
        self.assertTrue(by_hand.get_external_id()[by_hand.id].startswith("__export__"))

        # The tax by hand has no account and no negative factor: it is kept
        # and the log says so.
        with self.assertLogs(LOGGER_NAME, level="WARNING"):
            self._migrate()

        self.assertEqual(self._tax(key), by_hand)
        self.assertEqual(self._deductible_sale_taxes(group), by_hand)

    def test_migration_prefers_the_active_tax_by_hand(self):
        """An archived workaround is not adopted in place of the active one."""
        key = "tax_template_out_ibs_deductible"
        group = self._remove_deductible_sale_tax()
        archived = self._tax_by_hand(group, "IBS Dedutível antigo", active=False)
        active = self._tax_by_hand(group, "IBS Dedutível")
        self.assertLess(archived.id, active.id)

        # The tax by hand has no account and no negative factor: it is kept
        # and the log says so.
        with self.assertLogs(LOGGER_NAME, level="WARNING"):
            self._migrate()

        self.assertEqual(self._tax(key), active)
        self.assertTrue(active.active)
        self.assertFalse(archived.active)
        self.assertEqual(self._deductible_sale_taxes(group), archived | active)

    def test_migration_creates_the_chart_tax_when_only_archived_ones_exist(self):
        """The company is not left with no active deductible tax."""
        key = "tax_template_out_ibs_deductible"
        group = self._remove_deductible_sale_tax()
        archived = self._tax_by_hand(group, "IBS Dedutível antigo", active=False)

        with self.assertLogs(LOGGER_NAME, level="WARNING") as logs:
            self._migrate()

        chart_tax = self._tax(key)
        self.assertNotEqual(chart_tax, archived)
        self.assertTrue(chart_tax.active)
        self.assertTrue(chart_tax.deductible)
        self.assertFalse(archived.active)
        self.assertEqual(
            self._deductible_sale_taxes(group).filtered("active"), chart_tax
        )
        self.assertTrue(any("only archived" in line for line in logs.output))
        self.assertTrue(any("IBS Dedutível antigo" in line for line in logs.output))

    def test_migration_does_not_adopt_an_archived_tax_with_the_chart_name(self):
        """An archived tax with the name of the chart tax is left alone.

        The unique name rule of the taxes only looks at active taxes, so the
        chart tax is created beside the archived one and is the only active
        deductible sale tax of the company.
        """
        key = "tax_template_out_ibs_deductible"
        name = self._tax(key).name
        group = self._remove_deductible_sale_tax()
        archived = self._tax_by_hand(group, name, active=False)

        with self.assertLogs(LOGGER_NAME, level="WARNING") as logs:
            self._migrate()

        chart_tax = self._tax(key)
        self.assertNotEqual(chart_tax, archived)
        self.assertTrue(chart_tax.active)
        self.assertFalse(archived.active)
        self.assertEqual(
            self._deductible_sale_taxes(group).filtered("active"), chart_tax
        )
        self.assertFalse(any("matched by name only" in line for line in logs.output))

    def test_migration_warns_when_the_tax_kept_does_not_give_the_amount_back(self):
        """The tax by hand is kept, and the log says what it lacks."""
        key = "tax_template_out_ibs_deductible"
        group = self._remove_deductible_sale_tax()
        by_hand = self._tax_by_hand(group, "IBS Dedutível")

        with self.assertLogs(LOGGER_NAME, level="WARNING") as logs:
            self._migrate()

        self.assertEqual(self._tax(key), by_hand)
        self.assertTrue(any("negative factor" in line for line in logs.output))
        self.assertTrue(any("no account" in line for line in logs.output))

    def test_migration_warns_when_the_tax_matches_only_by_name(self):
        """A tax with the name but not the job is reused, with a warning."""
        key = "tax_template_out_ibs_deductible"
        generated = self._tax(key)
        name = generated.name
        generated.unlink()
        by_name = self.env["account.tax"].create(
            {
                "name": name,
                "company_id": self.company.id,
                "tax_group_id": self._tax("tax_template_out_icms").tax_group_id.id,
                "type_tax_use": "sale",
                "deductible": False,
                "amount": 0.0,
            }
        )

        with self.assertLogs(LOGGER_NAME, level="WARNING") as logs:
            self._migrate()

        self.assertEqual(self._tax(key), by_name)
        self.assertTrue(any("matched by name only" in line for line in logs.output))

    def test_migration_warns_when_there_are_many_taxes_by_hand(self):
        """The first tax of the job is kept and the others are reported."""
        key = "tax_template_out_ibs_deductible"
        generated = self._tax(key)
        group = generated.tax_group_id
        generated.unlink()
        taxes = self.env["account.tax"]
        for name in ("IBS A", "IBS B"):
            taxes |= self.env["account.tax"].create(
                {
                    "name": name,
                    "company_id": self.company.id,
                    "tax_group_id": group.id,
                    "type_tax_use": "sale",
                    "deductible": True,
                    "amount": 0.0,
                }
            )

        with self.assertLogs(LOGGER_NAME, level="WARNING") as logs:
            self._migrate()

        self.assertEqual(self._tax(key), taxes[0])
        self.assertTrue(any("IBS A" in line for line in logs.output))

    def test_migration_keeps_the_default_taxes_of_the_company(self):
        """Adding taxes to a company in use does not reset its default taxes."""
        sale_tax = self._tax("tax_template_out_icms")
        purchase_tax = self._tax("tax_template_in_icms")
        self.company.write(
            {
                "account_sale_tax_id": sale_tax.id,
                "account_purchase_tax_id": purchase_tax.id,
            }
        )
        self._remove_new_taxes()

        self._migrate()

        self.assertEqual(self.company.account_sale_tax_id, sale_tax)
        self.assertEqual(self.company.account_purchase_tax_id, purchase_tax)

    def test_migration_migrates_an_archived_company(self):
        """An archived company with the chart is migrated like the others.

        The many2many `company_ids` of an account reads only active
        companies, so the account created for an archived company looked as
        if it had no company and the constraint of the account failed.
        """
        archived = self._create_company(f"Empresa Arquivada {self.chart_template}")
        self._remove_new_taxes()
        archived_taxes = [self._tax(key, archived) for key in NEW_TAXES]
        archived_taxes += [self._tax(NEW_GROUP, archived)]
        for record in archived_taxes:
            record.unlink()
        for key in PLAIN_TAXES:
            for refund in (False, True):
                self._tax_line(
                    self._tax(key, archived), refund=refund
                ).account_id = False
        accounts = (
            self.env["account.account"]
            .with_company(archived)
            .search(
                [
                    ("company_ids", "in", archived.id),
                    ("code", "in", list(self.new_plan_account_codes)),
                ]
            )
        )
        accounts.unlink()
        archived.active = False
        self.assertFalse(self._tax(NEW_TAXES[0], archived))

        self._migrate()

        for key in NEW_TAXES:
            self.assertTrue(self._tax(key, archived), f"{key} was not created")
        for key in ALL_TAXES:
            self.assertTrue(
                self._tax_line(self._tax(key, archived)).account_id,
                f"{key} has no account",
            )
        self.assertTrue(self._tax(NEW_TAXES[0]), "the active company was skipped")

    def test_migration_uses_the_same_accounts_as_a_new_load(self):
        """A company migrated ends with the accounts of a company loaded now."""
        self._remove_new_taxes()
        self._remove_new_plan_accounts()

        self._migrate()

        fresh = self._create_company(f"Empresa Nova {self.chart_template}")

        def used_accounts(company):
            accounts = self.env["account.account"]
            for key in ALL_TAXES:
                tax = self._tax(key, company)
                for refund in (False, True):
                    accounts |= self._tax_line(tax, refund=refund).account_id
            return sorted(
                (account.with_company(company).code, account.name, account.account_type)
                for account in accounts
            )

        self.assertEqual(used_accounts(self.company), used_accounts(fresh))
        self.assertEqual(
            [
                (tax.name, *self._account_codes(tax))
                for tax in map(self._tax, ALL_TAXES)
            ],
            [
                (tax.name, *self._account_codes(tax, fresh))
                for tax in (self._tax(key, fresh) for key in ALL_TAXES)
            ],
        )
