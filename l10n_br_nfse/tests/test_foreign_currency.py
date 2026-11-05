# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_base.tests.tools import load_fixture_files
from odoo.addons.l10n_br_fiscal.tests.tools import load_fiscal_fixture_files

RATE = 4.9


class TestNfseForeignCurrency(TransactionCase):
    """NFS-e data of an invoice in foreign currency goes out in reais."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        load_fiscal_fixture_files(cls.env)
        load_fixture_files(
            cls.env, "l10n_br_fiscal", file_names=["fiscal_document_nfse_demo.xml"]
        )
        cls.nfse = cls.env.ref("l10n_br_fiscal.demo_nfse_same_state")
        cls.line = cls.nfse.fiscal_line_ids[0]
        cls.usd = cls.env.ref("base.USD")
        cls.line.write({"price_unit": 1000.0, "quantity": 1.0})
        now = fields.Datetime.now()
        cls.nfse.write({"document_date": now, "date_in_out": now})

    def _foreign(self):
        return patch.object(
            type(self.nfse),
            "_nfse_foreign_currency_rate",
            return_value=(self.usd, RATE),
        )

    def test_same_currency_changes_nothing(self):
        self.assertEqual(
            self.nfse._nfse_foreign_currency_rate(), (self.env["res.currency"], 1.0)
        )
        self.assertEqual(self.nfse._nfse_foreign_trade_data(), {})
        self.assertNotIn("comercio_exterior", self.nfse._prepare_dados_servico())
        self.assertEqual(
            self.line._prepare_line_service(),
            self.line._prepare_line_service(rate=1.0),
        )

    def test_line_values_are_converted_before_rounding(self):
        original = self.line._prepare_line_service()
        converted = self.line._prepare_line_service(rate=RATE)
        self.assertEqual(
            converted["valor_servicos"], round(self.line.price_gross * RATE, 2)
        )
        self.assertEqual(
            converted["valor_liquido_nfse"], round(self.line.amount_taxed * RATE, 2)
        )
        # rates are not converted
        self.assertEqual(converted["aliquota"], original["aliquota"])

    def test_iss_is_recomputed_from_the_converted_base(self):
        self.line.issqn_percent = 5.0
        self.line.issqn_value = 50.0
        converted = self.line._prepare_line_service(rate=RATE)
        self.assertEqual(
            converted["valor_iss"],
            round(converted["base_calculo"] * 5.0 / 100, 2),
        )

    def test_service_data_and_foreign_trade_group(self):
        with self._foreign():
            service = self.nfse._prepare_dados_servico()
            rps = self.nfse._prepare_lote_rps()
        self.assertEqual(
            service["valor_servicos"], round(self.line.price_gross * RATE, 2)
        )
        foreign = service["comercio_exterior"]
        self.assertEqual(foreign["moeda_original"], "USD")
        self.assertEqual(foreign["codigo_moeda"], "220")
        self.assertEqual(
            foreign["valor_servico_moeda_original"], round(self.line.price_gross, 2)
        )
        self.assertEqual(foreign["taxa_cambio"], RATE)
        self.assertEqual(foreign["modo_prestacao"], "1")
        self.nfse.nfse_foreign_trade_mode = "4"
        with self._foreign():
            foreign = self.nfse._prepare_dados_servico()["comercio_exterior"]
        self.assertEqual(foreign["modo_prestacao"], "4")
        self.assertEqual(
            rps["total_recebido"], round(self.nfse.amount_price_gross * RATE, 2)
        )
        self.assertIn("USD", rps["customer_additional_data"])
