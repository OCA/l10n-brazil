# Copyright (C) 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
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

DUIMP_GENERAL_DATA = {
    "identificacao": {"numero": "26BR0000758808", "versao": 1},
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
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.company_data["company"]
        nfe_group = cls.env.ref("l10n_br_nfe.group_manager", raise_if_not_found=False)
        if nfe_group:
            cls.env.user.groups_id |= nfe_group
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
                "duimp_number": "26BR0000758808",
                "fiscal_operation_id": self.fiscal_operation.id,
            }
        )

    def _consult_wizard(self, webservice=None):
        wizard = self._create_wizard()
        fake = webservice or FakeDuimpWebservice()
        with patch.object(ResCompany, "_get_duimp_webservice", new=lambda self: fake):
            wizard.action_consult_duimp()
        return wizard

    def test_consult_and_import_duimp(self):
        """Query a DUIMP, match its item to a product/CFOP, import it,
        and confirm the imported tax values survive a save untouched.
        """
        wizard = self._consult_wizard()

        self.assertEqual(len(wizard.duimp_line_ids), 1)
        line = wizard.duimp_line_ids[0]
        self.assertEqual(line.quantity, 846.0)
        self.assertAlmostEqual(line.customs_value, 145600.16)
        self.assertAlmostEqual(line.freight_value, 11947.04)
        self.assertAlmostEqual(line.insurance_value, 720.13)
        # the exporter name matches an existing partner, so it is
        # auto-matched by _search_partner during _fill_wizard_from_duimp:
        self.assertEqual(wizard.partner_id, self.partner)

        line.product_id = self.product
        line.cfop_id = self.cfop

        action = wizard.action_import_duimp()
        move = self.env["account.move"].browse(action["res_id"])

        self.assertTrue(move.fiscal_document_id.imported_document)
        self.assertEqual(move.fiscal_document_id.duimp_number, "26BR0000758808")
        fiscal_lines = move.fiscal_document_id.fiscal_line_ids
        self.assertEqual(len(fiscal_lines), 1)
        fiscal_line = fiscal_lines[0]
        self.assertAlmostEqual(fiscal_line.ii_base, 145600.16, places=2)
        self.assertAlmostEqual(fiscal_line.ii_value, 20625.01, places=2)
        self.assertAlmostEqual(fiscal_line.ipi_value, 11095.51, places=2)
        self.assertAlmostEqual(fiscal_line.pis_value, 3057.61, places=2)
        self.assertAlmostEqual(fiscal_line.cofins_value, 14115.22, places=2)

        fiscal_line.write({"quantity": fiscal_line.quantity})
        self.assertAlmostEqual(fiscal_line.ii_value, 20625.01, places=2)

    def test_onchange_duimp_number_resets_lines(self):
        wizard = self._consult_wizard()
        self.assertTrue(wizard.duimp_line_ids)
        self.assertTrue(wizard.duimp_raw_json)

        wizard.duimp_number = "26BR0000000000"
        wizard._onchange_duimp_number()

        self.assertFalse(wizard.duimp_line_ids)
        self.assertFalse(wizard.duimp_raw_json)

    def test_action_consult_duimp_requires_number(self):
        wizard = self._create_wizard()
        wizard.duimp_number = False
        with self.assertRaises(UserError):
            wizard.action_consult_duimp()

    def test_action_import_duimp_validations(self):
        with self.subTest(scenario="no_lines"):
            wizard = self._create_wizard()
            with self.assertRaises(UserError):
                wizard.action_import_duimp()

        with self.subTest(scenario="no_partner"):
            wizard = self._consult_wizard()
            wizard.partner_id = False
            wizard.duimp_line_ids.product_id = self.product
            wizard.duimp_line_ids.cfop_id = self.cfop
            with self.assertRaises(UserError):
                wizard.action_import_duimp()

        with self.subTest(scenario="no_product"):
            wizard = self._consult_wizard()
            wizard.duimp_line_ids.cfop_id = self.cfop
            with self.assertRaises(UserError):
                wizard.action_import_duimp()

        with self.subTest(scenario="no_cfop"):
            wizard = self._consult_wizard()
            wizard.duimp_line_ids.product_id = self.product
            with self.assertRaises(UserError):
                wizard.action_import_duimp()

    def test_duimp_exporter_name_fallbacks(self):
        wizard = self._create_wizard()

        with self.subTest(case="no_items"):
            self.assertFalse(wizard._duimp_exporter_name([]))

        with self.subTest(case="fabricante_fallback"):
            name = wizard._duimp_exporter_name(
                [{"dadosOperadorFabricante": {"nome": "FAB LTDA"}}]
            )
            self.assertEqual(name, "FAB LTDA")

        with self.subTest(case="nome_operador_fallback"):
            name = wizard._duimp_exporter_name(
                [{"dadosOperadorExportador": {"nomeOperador": "OP LTDA"}}]
            )
            self.assertEqual(name, "OP LTDA")

    def test_consult_without_exporter_name_leaves_partner_unset(self):
        """A DUIMP whose items carry no exporter/manufacturer name still
        fills the item grid; only the vendor lookup is skipped, since
        there is no name to search a partner with.
        """
        item = {
            key: value
            for key, value in DUIMP_ITEMS[0].items()
            if key != "dadosOperadorExportador"
        }
        wizard = self._consult_wizard(FakeDuimpWebservice(items=[item]))

        self.assertFalse(wizard.issuer_legal_name)
        self.assertFalse(wizard.partner_id)
        self.assertEqual(len(wizard.duimp_line_ids), 1)
        self.assertEqual(wizard.duimp_line_ids.product_code, "102")

    def test_prepare_duimp_line_values_zero_quantity(self):
        wizard = self._create_wizard()
        item = {
            "numeroItem": "9",
            "dadosProduto": {},
            "itemTributo": {
                "dadosMercadoria": {"quantidadeUnidadeComercializada": 0.0},
                "valorMercadoria": {},
            },
        }
        values = wizard._prepare_duimp_line_values(item)
        self.assertEqual(values["quantity"], 0.0)
        self.assertEqual(values["price_unit"], 0.0)

    def test_get_document_serie_reuses_existing(self):
        wizard = self._create_wizard()
        serie_model = self.env["l10n_br_fiscal.document.serie"]
        domain = [
            ("company_id", "=", self.company.id),
            ("document_type_id", "=", self.env.ref("l10n_br_fiscal.document_55").id),
        ]
        before = serie_model.search_count(domain)

        first = wizard._get_document_serie()
        second = wizard._get_document_serie()

        self.assertEqual(first, second)
        self.assertEqual(serie_model.search_count(domain), before + 1)

    def test_zero_customs_value_allocation(self):
        """When every item has a zero customs value, both the
        proportion (denominator) and the per-tax percent (base) fall
        back to their else-branches instead of raising ZeroDivisionError.
        """
        wizard = self._consult_wizard(FakeDuimpWebservice(items=DUIMP_ITEMS_ZERO_VALUE))
        wizard.duimp_line_ids.product_id = self.product
        wizard.duimp_line_ids.cfop_id = self.cfop

        action = wizard.action_import_duimp()
        move = self.env["account.move"].browse(action["res_id"])
        fiscal_line = move.fiscal_document_id.fiscal_line_ids
        self.assertEqual(fiscal_line.ii_base, 0.0)
        self.assertEqual(fiscal_line.ii_percent, 0.0)
        self.assertEqual(fiscal_line.afrmm_value, 0.0)

    def test_multi_item_afrmm_allocation(self):
        """AFRMM and tax totals are allocated proportionally to each
        item's customs value when there is more than one line.
        """
        wizard = self._consult_wizard(FakeDuimpWebservice(items=DUIMP_ITEMS_TWO))
        self.assertEqual(len(wizard.duimp_line_ids), 2)
        wizard.duimp_afrmm_value = 1000.0
        line_1, line_2 = wizard.duimp_line_ids
        line_1.product_id = self.product
        line_1.cfop_id = self.cfop
        line_2.product_id = self.product_2
        line_2.cfop_id = self.cfop

        action = wizard.action_import_duimp()
        move = self.env["account.move"].browse(action["res_id"])
        fiscal_lines = move.fiscal_document_id.fiscal_line_ids.sorted("id")
        self.assertEqual(len(fiscal_lines), 2)

        self.assertAlmostEqual(fiscal_lines[0].afrmm_value, 800.0, places=2)
        self.assertAlmostEqual(fiscal_lines[1].afrmm_value, 200.0, places=2)
        self.assertAlmostEqual(fiscal_lines[0].ii_value, 20625.01 * 0.8, places=2)
        self.assertAlmostEqual(fiscal_lines[1].ii_value, 20625.01 * 0.2, places=2)
