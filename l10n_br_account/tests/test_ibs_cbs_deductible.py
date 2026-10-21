# Copyright 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import importlib.util

from odoo import Command
from odoo.modules.module import get_module_path
from odoo.tests import tagged

from odoo.addons.l10n_br_coa.models.template_br_oca import BR_CHARTS
from odoo.addons.l10n_br_coa.tests.common import (
    NEW_GROUP,
    NEW_TAXES,
    load_migration,
)

from .common import AccountMoveBRCommon

# Tax -> (invoice account, refund account), without the review suffix. The
# codes are the ones of l10n_br_coa_generic.
EXPECTED_ACCOUNTS = {
    "tax_template_out_ibs": ("2.1.7.1.14", "1.1.4.1.12"),
    "tax_template_in_ibs": ("1.1.4.1.12", "2.1.7.1.14"),
    "tax_template_out_cbs": ("2.1.7.1.15", "1.1.4.1.13"),
    "tax_template_in_cbs": ("1.1.4.1.13", "2.1.7.1.15"),
    "tax_template_out_is": ("2.1.7.1.16", "1.1.4.1.14"),
    "tax_template_in_is": ("1.1.4.1.14", "2.1.7.1.16"),
    "tax_template_out_ibs_deductible": ("6.1.1.2.12", "6.1.1.2.32"),
    "tax_template_in_ibs_deductible": ("6.1.1.2.12", "2.1.7.1.14"),
    "tax_template_out_cbs_deductible": ("6.1.1.2.13", "6.1.1.2.33"),
    "tax_template_in_cbs_deductible": ("6.1.1.2.13", "2.1.7.1.15"),
    "tax_template_out_is_deductible": ("6.1.1.2.14", "6.1.1.2.34"),
    "tax_template_in_is_deductible": ("6.1.1.2.14", "2.1.7.1.16"),
}


@tagged("post_install", "-at_install")
class TestIbsCbsDeductible(AccountMoveBRCommon):
    """IBS and CBS must not inflate the receivable of a deductible operation.

    When the fiscal operation uses deductible taxes the product line takes
    the full document total, and the deductible account tax of each fiscal
    tax gives the amount back with a negative factor. The chart shipped by
    `l10n_br_coa` has to carry the deductible IBS and CBS taxes, otherwise
    the tax is added once more to the receivable and the invoice total no
    longer matches the title.
    """

    chart_template = "generic_coa"
    # The core chart has none of the Brazilian codes: `load_fiscal_taxes`
    # creates the tax accounts with the review suffix. The accounts of the
    # Brazilian charts (no suffix) are tested in l10n_br_coa_generic and
    # l10n_br_coa_simple, which load those charts in a company of their own.
    account_suffix = ".BR"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The complex_tax of the core fixture (a group and its two children) is
        # not a fiscal tax. The children are created in the first tax group of
        # the company, which on a Brazilian chart is a fiscal group, so
        # `FiscalTax._account_taxes` (it picks the account taxes by group) puts
        # them on every fiscal line. The fiscal total ignores them and the core
        # adds their lines: the entry is unbalanced by 65.00.
        cls.env["account.tax"].with_context(active_test=False).search(
            [("name", "like", "complex_tax")]
        ).unlink()
        cls.company = cls.company_data["company"]
        cls.env["account.chart.template"].load_fiscal_taxes(companies=[cls.company])
        cls.configure_normal_company_taxes()
        tax_def_model = cls.env["l10n_br_fiscal.tax.definition"]
        for group, tax, cst in (
            ("ibs", "tax_ibs_0_1", "cst_ibs_000"),
            ("cbs", "tax_cbs_0_9", "cst_cbs_000"),
        ):
            tax_def_model.create(
                {
                    "company_id": cls.company.id,
                    "tax_group_id": cls.env.ref(f"l10n_br_fiscal.tax_group_{group}").id,
                    "is_taxed": True,
                    "is_debit_credit": True,
                    "custom_tax": True,
                    "tax_id": cls.env.ref(f"l10n_br_fiscal.{tax}").id,
                    "cst_id": cls.env.ref(f"l10n_br_fiscal.{cst}").id,
                    "state": "approved",
                }
            )
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.operation.with_company(cls.company).deductible_taxes = True
        cls.term_3x = cls.env["account.payment.term"].create(
            {
                "name": "3 parcelas",
                "company_id": cls.company.id,
                "line_ids": [
                    Command.create(
                        {"value": "percent", "value_amount": 33.33, "nb_days": 30}
                    ),
                    Command.create(
                        {"value": "percent", "value_amount": 33.33, "nb_days": 60}
                    ),
                    Command.create(
                        {"value": "percent", "value_amount": 33.34, "nb_days": 90}
                    ),
                ],
            }
        )

    def _sale_move(self):
        return self.init_invoice(
            "out_invoice",
            products=[self.product_a],
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=self.empresa_lc_document_55_serie_1,
            fiscal_operation=self.operation,
            fiscal_operation_lines=[self.env.ref("l10n_br_fiscal.fo_venda_venda")],
        )

    def _product_line(self, move):
        return move.invoice_line_ids.filtered(lambda line: line.product_id)[:1]

    def _tax(self, key):
        return self.env.ref(
            f"l10n_br_coa.{self.company.id}_{key}", raise_if_not_found=False
        ) or self.env.ref(f"account.{self.company.id}_{key}", raise_if_not_found=False)

    def _account_code(self, tax, refund=False):
        lines = (
            tax.refund_repartition_line_ids
            if refund
            else tax.invoice_repartition_line_ids
        )
        line = lines.filtered(lambda rline: rline.repartition_type == "tax")
        return line.account_id.with_company(self.company).code

    def test_chart_has_the_deductible_taxes(self):
        """The chart carries IBS, CBS and IS, plain and deductible."""
        for key, (invoice_code, refund_code) in EXPECTED_ACCOUNTS.items():
            tax = self._tax(key)
            self.assertTrue(tax, f"{key} is missing from the chart")
            deductible = "deductible" in key
            self.assertEqual(tax.deductible, deductible)
            line = tax.invoice_repartition_line_ids.filtered(
                lambda rline: rline.repartition_type == "tax"
            )
            self.assertEqual(
                line.factor_percent,
                -100 if deductible else 100,
                f"{key} has the wrong repartition factor",
            )
            self.assertEqual(
                self._account_code(tax),
                invoice_code + self.account_suffix,
                f"{key}: invoice account",
            )
            self.assertEqual(
                self._account_code(tax, refund=True),
                refund_code + self.account_suffix,
                f"{key}: refund account",
            )

    def test_receivable_equals_invoice_total(self):
        """With deductible taxes the title is the invoice total."""
        move = self._sale_move()
        line = self._product_line(move)
        # Guard: IBS and CBS are really computed, or the test proves nothing.
        self.assertTrue(line.ibs_value, "IBS was not computed")
        self.assertTrue(line.cbs_value, "CBS was not computed")
        self.assertTrue(
            line.tax_ids.filtered(lambda tax: tax.deductible and "IBS" in tax.name),
            "the deductible IBS tax is not on the line",
        )
        move.action_post()
        self.assertEqual(move.state, "posted")
        self.assertAlmostEqual(move.amount_residual, move.amount_total, places=2)
        # IBS and CBS are owed ("a Recolher") and the deductible tax gives the
        # amount back in the revenue deduction ("s/ Vendas").
        codes = set(move.line_ids.account_id.with_company(self.company).mapped("code"))
        for code in ("2.1.7.1.14", "2.1.7.1.15", "6.1.1.2.12", "6.1.1.2.13"):
            self.assertIn(code + self.account_suffix, codes)

    def test_payment_term_in_three_installments_posts(self):
        """Splitting the title in three keeps the entry balanced."""
        move = self._sale_move()
        move.invoice_payment_term_id = self.term_3x
        move.action_post()
        self.assertEqual(move.state, "posted")
        receivable = move.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )
        self.assertEqual(len(receivable), 3)
        self.assertAlmostEqual(
            sum(receivable.mapped("balance")), move.amount_total, places=2
        )
        self.assertAlmostEqual(move.amount_residual, move.amount_total, places=2)

    def test_coa_migration_names_the_records_like_load_fiscal_taxes(self):
        """On a chart that is not Brazilian the new records are not `account.`.

        `load_fiscal_taxes` names the Brazilian taxes `l10n_br_coa.<company>_...`;
        the migration of `l10n_br_coa` has to do the same, or it leaves
        xmlids of the Brazilian chart in the namespace of the `account` module.
        """
        keys = [NEW_GROUP, *NEW_TAXES]
        for key in NEW_TAXES:
            self._tax(key).unlink()
        self._tax(NEW_GROUP).unlink()
        self.assertFalse(self._tax(NEW_TAXES[0]))

        load_migration().migrate_companies(self.env(su=True))
        self.env.invalidate_all()

        names = [f"{self.company.id}_{key}" for key in keys]
        records = self.env["ir.model.data"].search(
            [
                ("name", "in", names),
                ("model", "in", ("account.tax", "account.tax.group")),
            ]
        )
        self.assertEqual(len(records), len(keys))
        # A Brazilian chart names its records `account.<company>_...`, as the
        # chart load does; any other chart gets the module of `load_fiscal_taxes`.
        module = (
            "account" if self.company.chart_template in BR_CHARTS else "l10n_br_coa"
        )
        self.assertEqual(set(records.mapped("module")), {module})

    def test_migration_links_the_is_group_to_the_fiscal_group(self):
        """Only the IS group is linked; the other groups are left alone."""
        # The folder of a migration is named after the version (`18.0.3.9.0`)
        # and the file has a dash (`post-migration.py`): neither is a valid
        # module name, so a plain `import` cannot reach it. It is loaded by
        # path; it is the same file Odoo runs on `-u`.
        path = get_module_path("l10n_br_account")
        spec = importlib.util.spec_from_file_location(
            "l10n_br_account_post_migration_18_0_3_9_0",
            f"{path}/migrations/18.0.3.9.0/post-migration.py",
        )
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        group_is = self._tax(NEW_GROUP)
        group_issqn = self._tax("tax_group_issqn")
        fiscal_issqn = group_issqn.fiscal_tax_group_id
        self.assertEqual(
            group_is.fiscal_tax_group_id, self.env.ref("l10n_br_fiscal.tax_group_is")
        )
        group_is.fiscal_tax_group_id = False
        group_issqn.fiscal_tax_group_id = False

        # `link_is_groups` is the body of `migrate`: the openupgrade decorator
        # logs an ERROR when Odoo is not the caller, which fails the CI log
        # check.
        migration.link_is_groups(self.env(su=True))
        self.env.invalidate_all()

        self.assertEqual(
            group_is.fiscal_tax_group_id, self.env.ref("l10n_br_fiscal.tax_group_is")
        )
        self.assertFalse(group_issqn.fiscal_tax_group_id)
        self.assertTrue(fiscal_issqn)


@tagged("post_install", "-at_install")
class TestIbsCbsDeductibleGenericChart(TestIbsCbsDeductible):
    """Same flows with the Brazilian generic chart: no suffix on the accounts."""

    # The tests are inherited from the class above: Odoo only collects them
    # from the subclass when it asks for the inherited ones.
    allow_inherited_tests_method = True
    chart_template = "br_oca_generic"
    account_suffix = ""
