# Copyright (C) 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

"""Fixtures reproduce the shape of the Portal Único Siscomex DUIMP API
responses (see models/duimp_webservice.py) using the tax/value totals of
a real single-item DUIMP extract, so that the expected line-level values
(allocation proportion == 1.0) match the document totals exactly.
"""

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon
from odoo.addons.l10n_br_duimp.models.res_company import ResCompany
from odoo.addons.l10n_br_duimp.tests.common import (
    DUIMP_NUMBER,
    grant_nfe_access,
)

DUIMP_GENERAL_DATA = {
    "identificacao": {"numero": DUIMP_NUMBER, "versao": 1},
    "tributos": {
        "tributosCalculados": [
            {"tipo": "II", "valoresBRL": {"devido": 20625.01}},
            {"tipo": "IPI", "valoresBRL": {"devido": 11095.51}},
            {"tipo": "PIS", "valoresBRL": {"devido": 3057.61}},
            {"tipo": "COFINS", "valoresBRL": {"devido": 14115.22}},
            {"tipo": "TAXA_UTILIZACAO", "valoresBRL": {"devido": 223.64}},
        ]
    },
}

DUIMP_ITEMS = [
    {
        "numeroItem": "1",
        "dadosProduto": {"codigoProduto": "102", "codigoNCM": "39191090"},
        "dadosOperadorExportador": {"nome": "DENSO GMBH"},
        "itemTributo": {
            "dadosMercadoria": {
                "quantidadeUnidadeComercializada": 846.0,
                "unidadeComercializada": "UN",
            },
            "valorMercadoria": {
                "valorMercadoria": 67529.75,
                "valorFreteRateado": 11947.04,
                "valorSeguroRateado": 720.13,
                "valorAduaneiro": 145600.16,
            },
        },
    }
]

DUIMP_ITEMS_TWO = [
    {
        "numeroItem": "1",
        "dadosProduto": {"codigoProduto": "102", "codigoNCM": "39191090"},
        "dadosOperadorExportador": {"nome": "DENSO GMBH"},
        "itemTributo": {
            "dadosMercadoria": {
                "quantidadeUnidadeComercializada": 800.0,
                "unidadeComercializada": "UN",
            },
            "valorMercadoria": {
                "valorMercadoria": 60000.0,
                "valorFreteRateado": 9000.0,
                "valorSeguroRateado": 500.0,
                "valorAduaneiro": 80000.0,
            },
        },
    },
    {
        "numeroItem": "2",
        "dadosProduto": {"codigoProduto": "103", "codigoNCM": "39191090"},
        "dadosOperadorExportador": {"nome": "DENSO GMBH"},
        "itemTributo": {
            "dadosMercadoria": {
                "quantidadeUnidadeComercializada": 200.0,
                "unidadeComercializada": "UN",
            },
            "valorMercadoria": {
                "valorMercadoria": 15000.0,
                "valorFreteRateado": 2000.0,
                "valorSeguroRateado": 100.0,
                "valorAduaneiro": 20000.0,
            },
        },
    },
]

DUIMP_ITEMS_ZERO_VALUE = [
    {
        "numeroItem": "1",
        "dadosProduto": {"codigoProduto": "999", "codigoNCM": "00000000"},
        "dadosOperadorExportador": {"nome": "DENSO GMBH"},
        "itemTributo": {
            "dadosMercadoria": {
                "quantidadeUnidadeComercializada": 10.0,
                "unidadeComercializada": "UN",
            },
            "valorMercadoria": {
                "valorMercadoria": 500.0,
                "valorAduaneiro": 0.0,
                "valorFreteRateado": 0.0,
                "valorSeguroRateado": 0.0,
            },
        },
    }
]


class FakeDuimpWebservice:
    """Stands in for models.duimp_webservice.DuimpWebservice so tests
    never perform a real network/mTLS call."""

    def __init__(self, general_data=None, items=None):
        self.general_data = (
            general_data if general_data is not None else DUIMP_GENERAL_DATA
        )
        self.items = items if items is not None else DUIMP_ITEMS

    def get_general_data(self, duimp_number, duimp_version=None):
        return self.general_data

    def get_items(self, duimp_number, duimp_version=None, offset=0, limit=500):
        return self.items


@tagged("post_install", "-at_install")
class TestDuimpImportWizard(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref or "l10n_br_coa.l10n_br_coa_template")
        grant_nfe_access(cls.env)
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.company_data["company"]
        cls.product = cls.env["product.product"].create(
            {
                "name": "DENSOLEN-AS39 P BLACK",
                "type": "consu",
                "purchase_ok": True,
                "default_code": "102",
            }
        )
        cls.product_2 = cls.env["product.product"].create(
            {
                "name": "DENSOLEN-R20 HT WHITE",
                "type": "consu",
                "purchase_ok": True,
                "default_code": "103",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "DENSO GMBH",
                "is_company": True,
                "country_id": cls.env.ref("base.de").id,
            }
        )
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.cfop = cls.env.ref("l10n_br_fiscal.cfop_3102")

    def _create_wizard(self):
        return self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "company_id": self.company.id,
                "duimp_number": DUIMP_NUMBER,
                "fiscal_operation_id": self.fiscal_operation.id,
            }
        )

    def _consult_wizard(self, webservice=None):
        """Runs action_consult_duimp and returns the persistent DUIMP
        declaration it created/refreshed."""
        wizard = self._create_wizard()
        fake = webservice or FakeDuimpWebservice()
        with patch.object(ResCompany, "_get_duimp_webservice", new=lambda self: fake):
            action = wizard.action_consult_duimp()
        return self.env["l10n_br_duimp.declaracao"].browse(action["res_id"])

    def test_consult_creates_persistent_declaracao(self):
        declaracao = self._consult_wizard()
        self.assertTrue(declaracao.exists())
        self.assertEqual(declaracao.numero, DUIMP_NUMBER)
        self.assertEqual(declaracao.versao, 1)
        self.assertEqual(declaracao.state, "open")
        self.assertEqual(len(declaracao.item_ids), 1)
        item = declaracao.item_ids
        self.assertEqual(item.quantidade, 846.0)
        self.assertAlmostEqual(item.valor_aduaneiro, 145600.16)
        self.assertAlmostEqual(item.valor_frete_rateado, 11947.04)
        self.assertAlmostEqual(item.valor_seguro_rateado, 720.13)
        # products are auto-matched by codigoProduto == default_code
        self.assertEqual(item.product_id, self.product)
        # the exporter name matches an existing partner (best-effort)
        self.assertEqual(declaracao.fornecedor_partner_id, self.partner)
        # header federal taxes
        self.assertAlmostEqual(declaracao.ii_total, 20625.01)
        self.assertAlmostEqual(declaracao.cofins_total, 14115.22)

    def test_consult_and_generate_invoice(self):
        """Query a DUIMP, match its item to a product/CFOP, generate the
        vendor bill, and confirm the imported tax values survive a save
        untouched. Single item => allocation proportion == 1.0, so the
        line values match the header totals exactly.
        """
        declaracao = self._consult_wizard()
        declaracao.item_ids.cfop_id = self.cfop

        action = declaracao.action_generate_vendor_bill()
        move = self.env["account.move"].browse(action["res_id"])

        self.assertEqual(declaracao.state, "locked")
        self.assertEqual(declaracao.account_move_id, move)
        self.assertTrue(move.fiscal_document_id.imported_document)
        self.assertEqual(move.fiscal_document_id.duimp_number, DUIMP_NUMBER)
        self.assertEqual(move.fiscal_document_id.duimp_declaracao_id, declaracao)
        fiscal_lines = move.fiscal_document_id.fiscal_line_ids
        self.assertEqual(len(fiscal_lines), 1)
        fiscal_line = fiscal_lines[0]
        self.assertEqual(fiscal_line.duimp_item_id, declaracao.item_ids)
        self.assertAlmostEqual(fiscal_line.ii_base, 145600.16, places=2)
        self.assertAlmostEqual(fiscal_line.ii_value, 20625.01, places=2)
        self.assertAlmostEqual(fiscal_line.ipi_value, 11095.51, places=2)
        self.assertAlmostEqual(fiscal_line.pis_value, 3057.61, places=2)
        self.assertAlmostEqual(fiscal_line.cofins_value, 14115.22, places=2)

        fiscal_line.write({"quantity": fiscal_line.quantity})
        self.assertAlmostEqual(fiscal_line.ii_value, 20625.01, places=2)

    def test_two_items_header_tax_allocation(self):
        """Without a per-item tax breakdown in the payload, the header
        totals are allocated by customs value (80000/100000 and
        20000/100000)."""
        declaracao = self._consult_wizard(
            webservice=FakeDuimpWebservice(items=DUIMP_ITEMS_TWO)
        )
        declaracao.item_ids.cfop_id = self.cfop

        action = declaracao.action_generate_vendor_bill()
        move = self.env["account.move"].browse(action["res_id"])
        fiscal_lines = move.fiscal_document_id.fiscal_line_ids
        self.assertEqual(len(fiscal_lines), 2)
        line_1 = fiscal_lines.filtered(lambda line: line.product_id == self.product)
        line_2 = fiscal_lines.filtered(lambda line: line.product_id == self.product_2)
        self.assertAlmostEqual(line_1.ii_value, 20625.01 * 0.8, places=2)
        self.assertAlmostEqual(line_2.ii_value, 20625.01 * 0.2, places=2)
        self.assertAlmostEqual(line_1.ii_base, 80000.0, places=2)
        self.assertAlmostEqual(line_2.ii_base, 20000.0, places=2)

    def test_zero_customs_value(self):
        declaracao = self._consult_wizard(
            webservice=FakeDuimpWebservice(items=DUIMP_ITEMS_ZERO_VALUE)
        )
        item = declaracao.item_ids
        self.assertAlmostEqual(item.valor_aduaneiro, 0.0)
        self.assertAlmostEqual(item.amount_afrmm, 0.0)

    def test_consult_reuses_open_declaracao(self):
        first = self._consult_wizard()
        second = self._consult_wizard()
        self.assertEqual(first, second)

    def test_consult_wizard_costs_forwarded(self):
        wizard = self._create_wizard()
        wizard.duimp_afrmm_value = 1000.0
        wizard.duimp_siscomex_value = 223.64
        fake = FakeDuimpWebservice()
        with patch.object(ResCompany, "_get_duimp_webservice", new=lambda self: fake):
            action = wizard.action_consult_duimp()
        declaracao = self.env["l10n_br_duimp.declaracao"].browse(action["res_id"])
        self.assertAlmostEqual(declaracao.afrmm_total, 1000.0)
        self.assertAlmostEqual(declaracao.taxa_siscomex_total, 223.64)
        # single item receives the full allocation
        self.assertAlmostEqual(declaracao.item_ids.amount_afrmm, 1000.0, places=2)

    def test_action_consult_duimp_requires_number(self):
        wizard = self._create_wizard()
        wizard.duimp_number = False
        with self.assertRaises(UserError):
            wizard.action_consult_duimp()

    def test_generate_invoice_validations(self):
        with self.subTest(scenario="no_vendor"):
            declaracao = self._consult_wizard()
            declaracao.fornecedor_partner_id = False
            declaracao.item_ids.cfop_id = self.cfop
            with self.assertRaises(UserError):
                declaracao.action_generate_vendor_bill()

        with self.subTest(scenario="no_product"):
            declaracao = self._consult_wizard()
            declaracao.item_ids.product_id = False
            declaracao.item_ids.cfop_id = self.cfop
            with self.assertRaises(UserError):
                declaracao.action_generate_vendor_bill()

        with self.subTest(scenario="no_cfop"):
            declaracao = self._consult_wizard()
            declaracao.item_ids.cfop_id = False
            with self.assertRaises(UserError):
                declaracao.action_generate_vendor_bill()
