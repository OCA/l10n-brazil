# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Contract of the tax engine entry point.

These tests pin two properties of `compute_taxes` and its per-domain compute
methods that the current code does not hold. They are deliberately independent
of any fiscal configuration: they call the compute methods directly with a
well-formed tax dictionary, so a failure points at the engine and not at a
missing tax definition in the data.

Why this matters: `l10n_br_fiscal.document.line` and `account.tax.compute_all`
are two entry points into the same engine, and they do not pass the same
arguments. `compute_all` has no `icms_cst_id` parameter at all, so every call
coming from the accounting side reaches the compute methods without it.
"""

from unittest.mock import patch

from odoo.tests import TransactionCase

from ..models.tax import TAX_DICT_VALUES


class TestTaxEngineContract(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Resolved by search instead of by xml id on purpose: these tests exercise
        # the engine contract, so they must run on a database with or without demo
        # data.
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].search(
            [("country_id.code", "=", "BR"), ("state_id", "!=", False)], limit=1
        )
        cls.product = cls.env["product.product"].search(
            [("type", "!=", "service")], limit=1
        )
        cls.operation_line = cls.env["l10n_br_fiscal.operation.line"].search(
            [], limit=1
        )
        cls.tax_icmsfcp = cls.env["l10n_br_fiscal.tax"].search(
            [("tax_domain", "=", "icmsfcp")], limit=1
        )
        cls.tax_icms = cls.env["l10n_br_fiscal.tax"].search(
            [("tax_domain", "=", "icms"), ("percent_amount", ">", 0)], limit=1
        )

    def setUp(self):
        super().setUp()
        if not (self.partner and self.product and self.operation_line):
            self.skipTest("database without the minimum fiscal records")

    def _kwargs(self, **extra):
        """The arguments both entry points share."""
        values = {
            "company": self.company,
            "partner": self.partner,
            "product": self.product,
            "price_unit": 100.0,
            "quantity": 10.0,
            "fiscal_price": 100.0,
            "fiscal_quantity": 10.0,
            "operation_line": self.operation_line,
            "ncm": self.product.ncm_id,
        }
        values.update(extra)
        return values

    def _taxes_dict(self, domain, **overrides):
        """A tax dictionary shaped like the one `compute_taxes` builds."""
        entry = dict(TAX_DICT_VALUES)
        entry.update(overrides)
        return {domain: entry}

    def test_icmsfcp_without_icms_cst_id(self):
        """_compute_icmsfcp must not require `icms_cst_id` to be passed.

        `account.tax.compute_all` cannot pass it: the parameter does not exist in
        its signature. Today `kwargs.get("icms_cst_id")` returns None and the
        method dereferences `.code` on it, so the accounting entry point raises
        AttributeError inside the engine.
        """
        if not self.tax_icmsfcp:
            self.skipTest("no icmsfcp tax in the database")
        taxes_dict = self._taxes_dict("icmsfcp")
        taxes_dict["icms"] = dict(TAX_DICT_VALUES, base=1000.0)
        try:
            self.tax_icmsfcp._compute_icmsfcp(
                self.tax_icmsfcp, taxes_dict, **self._kwargs()
            )
        except AttributeError as error:
            self.fail(
                "_compute_icmsfcp requires icms_cst_id, which the accounting "
                "entry point cannot provide: %s" % error
            )

    def test_icmsfcp_with_and_without_icms_cst_id_agree(self):
        """The two entry points must compute the same FCP for the same line.

        One passes `icms_cst_id` (the fiscal line does), the other cannot (the
        accounting side does not have the parameter). A tax value that depends on
        which entry point was used means the fiscal document and the accounting
        entries disagree on the same line.
        """
        if not self.tax_icmsfcp:
            self.skipTest("no icmsfcp tax in the database")
        cst = self.env["l10n_br_fiscal.cst"].search(
            [("code", "=", "00"), ("tax_domain", "=", "icms")], limit=1
        )
        base_dict = {"icms": dict(TAX_DICT_VALUES, base=1000.0)}

        with_cst = self._taxes_dict("icmsfcp")
        with_cst.update({k: dict(v) for k, v in base_dict.items()})
        self.tax_icmsfcp._compute_icmsfcp(
            self.tax_icmsfcp, with_cst, **self._kwargs(icms_cst_id=cst)
        )

        without_cst = self._taxes_dict("icmsfcp")
        without_cst.update({k: dict(v) for k, v in base_dict.items()})
        self.tax_icmsfcp._compute_icmsfcp(
            self.tax_icmsfcp, without_cst, **self._kwargs()
        )

        self.assertEqual(
            with_cst["icmsfcp"].get("fcpst_value"),
            without_cst["icmsfcp"].get("fcpst_value"),
            "FCP-ST value depends on which entry point called the engine",
        )

    def test_compute_taxes_does_not_hide_programming_errors(self):
        """An AttributeError raised inside a compute method must propagate.

        `compute_taxes` wraps both the `getattr` lookup and the call to the
        compute method in the same `try`, so any AttributeError raised while
        computing a tax is caught and the generic formula is used instead. The
        document is then posted with a plausible but wrong tax value, with
        nothing in the log.
        """
        if not self.tax_icms:
            self.skipTest("no icms tax with a percentage in the database")
        marker = "raised on purpose by the test"

        def boom(*args, **kwargs):
            raise AttributeError(marker)

        with patch.object(
            type(self.tax_icms), "_compute_icms", side_effect=boom, create=True
        ), self.assertRaises(AttributeError, msg=marker):
            self.tax_icms.compute_taxes(**self._kwargs())
