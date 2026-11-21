# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_base.tests.tools import load_fixture_files
from odoo.addons.l10n_br_fiscal.tests.tools import load_fiscal_fixture_files


@tagged("post_install", "-at_install")
class TestAccountNfseForeignCurrency(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        load_fiscal_fixture_files(cls.env)
        load_fixture_files(
            cls.env, "l10n_br_fiscal", file_names=["fiscal_document_nfse_demo.xml"]
        )
        cls.nfse = cls.env.ref("l10n_br_fiscal.demo_nfse_same_state")
        cls.usd = cls.env.ref("base.USD")
        cls.company = cls.nfse.company_id
        cls.company.currency_id = cls.env.ref("base.BRL")

    def _link_invoice(self, currency, rate):
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.nfse.partner_id.id,
                "currency_id": currency.id,
                "company_id": self.company.id,
            }
        )
        self.nfse.move_ids = [(6, 0, move.ids)]
        # set the rate last and flush, so that no recompute overrides it
        move.write({"invoice_currency_rate": rate})
        move.flush_recordset()
        self.assertAlmostEqual(move.invoice_currency_rate, rate, places=10)
        return move

    def test_no_invoice_changes_nothing(self):
        self.assertEqual(self.nfse._nfse_foreign_currency_rate()[1], 1.0)

    def test_invoice_in_company_currency_changes_nothing(self):
        self._link_invoice(self.company.currency_id, 1.0)
        currency, rate = self.nfse._nfse_foreign_currency_rate()
        self.assertFalse(currency)
        self.assertEqual(rate, 1.0)

    def test_invoice_in_usd_uses_the_inverse_of_the_invoice_rate(self):
        # manual rate: 4.90 BRL per USD <=> 1 BRL = 1 / 4.90 USD
        self._link_invoice(self.usd, 1 / 4.9)
        currency, rate = self.nfse._nfse_foreign_currency_rate()
        self.assertEqual(currency, self.usd)
        self.assertAlmostEqual(rate, 4.9, places=8)
