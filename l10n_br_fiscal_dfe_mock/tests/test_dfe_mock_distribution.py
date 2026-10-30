# Copyright 2026 Engenere (<https://engenere.one>)
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import gzip
from datetime import datetime, timedelta
from unittest import mock

from lxml import etree

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase

from ..models.res_company import MockDfeClient

SAMPLE_RES_NFE = (
    '<resNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00">'
    "<chNFe>35260210588201000105550010000001231000001230</chNFe>"
    "<CNPJ>10588201000105</CNPJ>"
    "<xNome>Partner Mock Ltda</xNome>"
    "<vNF>5432.10</vNF>"
    "</resNFe>"
)

ACCESS_KEY = "35260210588201000105550010000001231000001230"
NFE_DFE_PROCESSOR = (
    "odoo.addons.l10n_br_nfe_dfe.models.res_company.ResCompany._dfe_get_processor"
)
DFE_DISTRIBUTION = (
    "odoo.addons.l10n_br_fiscal_dfe.models.res_company.ResCompany"
    "._dfe_document_distribution"
)


class TestDfeMockDistribution(TransactionCase):
    """Tests for the mock DF-e distribution processor on res.company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.company.sudo().write({"dfe_mock_mode": True})
        cls.manager = cls.env["res.users"].create(
            {
                "name": "DF-e Mock Manager",
                "login": "dfe_mock_manager",
                "company_id": cls.company.id,
                "company_ids": [(6, 0, cls.company.ids)],
                "groups_id": [
                    (4, cls.env.ref("base.group_user").id),
                    (4, cls.env.ref("l10n_br_fiscal.group_manager").id),
                ],
            }
        )

    def setUp(self):
        super().setUp()
        self.env["dfe.mock.nsu"].sudo().search(
            [("company_id", "=", self.company.id)]
        ).unlink()

    def _create_nsu(self, nsu, schema_type="resNFe", access_key=None, consumed=False):
        return self.env["dfe.mock.nsu"].create(
            {
                "nsu": nsu,
                "schema_type": schema_type,
                "xml_content": SAMPLE_RES_NFE,
                "access_key": access_key or ACCESS_KEY,
                "company_id": self.company.id,
                "consumed": consumed,
            }
        )

    # ── _dfe_get_processor ──────────────────────────────────────────────

    def test_get_processor_mock_mode_on(self):
        processor = self.company._dfe_get_processor("nfe")
        self.assertIsInstance(processor, MockDfeClient)

    def test_get_processor_mock_mode_off_delegates(self):
        self.company.sudo().write({"dfe_mock_mode": False})
        try:
            with mock.patch(NFE_DFE_PROCESSOR) as patched_super:
                patched_super.return_value = "real_client"
                result = self.company._dfe_get_processor("nfe")
            self.assertEqual(result, "real_client")
        finally:
            self.company.sudo().write({"dfe_mock_mode": True})

    def test_get_processor_other_fiscal_type_delegates(self):
        """The pool only holds NF-e payloads, so other types reach super()."""
        with self.assertRaises(NotImplementedError):
            self.company._dfe_get_processor("cte")

    # ── consultar_distribuicao ──────────────────────────────────────────

    def test_empty_pool_returns_no_documents(self):
        resp = self.company._dfe_get_processor("nfe").consultar_distribuicao(
            ultimo_nsu="000000000000000"
        )
        self.assertEqual(resp.resposta.cStat, "137")
        self.assertFalse(resp.resposta.loteDistDFeInt.docZip)

    def test_pagination_returns_and_consumes_documents(self):
        record = self._create_nsu("000000000000001")
        resp = self.company._dfe_get_processor("nfe").consultar_distribuicao(
            ultimo_nsu="000000000000000"
        )
        self.assertEqual(resp.resposta.cStat, "138")
        self.assertEqual(resp.resposta.ultNSU, "000000000000001")
        doc_zips = resp.resposta.loteDistDFeInt.docZip
        self.assertEqual(len(doc_zips), 1)
        self.assertEqual(doc_zips[0].NSU, "000000000000001")
        self.assertEqual(doc_zips[0].schema, "resNFe_v1.00.xsd")
        self.assertEqual(
            gzip.decompress(doc_zips[0].value).decode("utf-8"), SAMPLE_RES_NFE
        )
        self.assertTrue(record.consumed)

    def test_pagination_skips_consumed_documents(self):
        self._create_nsu("000000000000001", consumed=True)
        resp = self.company._dfe_get_processor("nfe").consultar_distribuicao(
            ultimo_nsu="000000000000000"
        )
        self.assertEqual(resp.resposta.cStat, "137")

    def test_specific_search_by_access_key_does_not_consume(self):
        record = self._create_nsu("000000000000001")
        resp = self.company._dfe_get_processor("nfe").consultar_distribuicao(
            chave=ACCESS_KEY
        )
        self.assertEqual(resp.resposta.cStat, "138")
        self.assertEqual(len(resp.resposta.loteDistDFeInt.docZip), 1)
        self.assertFalse(record.consumed)

    def test_specific_search_by_nsu_does_not_consume(self):
        record = self._create_nsu("000000000000007")
        resp = self.company._dfe_get_processor("nfe").consultar_distribuicao(
            nsu_especifico="000000000000007"
        )
        self.assertEqual(resp.resposta.cStat, "138")
        self.assertFalse(record.consumed)

    # ── cooldown bypass while mocking ───────────────────────────────────

    def test_action_distribution_skips_cooldown_in_mock_mode(self):
        self.company.sudo().write(
            {"nfe_dfe_next_query": fields.Datetime.now() + timedelta(hours=1)}
        )
        with mock.patch(DFE_DISTRIBUTION) as patched:
            patched.return_value = "ran"
            result = self.company.action_document_distribution("nfe")
        patched.assert_called_once()
        self.assertEqual(result, "ran")
        self.assertFalse(self.company.nfe_dfe_next_query)

    def test_action_distribution_keeps_cooldown_when_mock_off(self):
        next_query = fields.Datetime.now() + timedelta(hours=1)
        self.company.sudo().write(
            {"dfe_mock_mode": False, "nfe_dfe_next_query": next_query}
        )
        try:
            with mock.patch(DFE_DISTRIBUTION) as patched:
                result = self.company.action_document_distribution("nfe")
            patched.assert_not_called()
            self.assertEqual(result.get("tag"), "display_notification")
            self.assertEqual(self.company.nfe_dfe_next_query, next_query)
        finally:
            self.company.sudo().write({"dfe_mock_mode": True})

    def test_action_distribution_other_fiscal_type_keeps_cooldown(self):
        next_query = fields.Datetime.now() + timedelta(hours=1)
        self.company.sudo().write({"nfe_dfe_next_query": next_query})
        with mock.patch(DFE_DISTRIBUTION):
            self.company.action_document_distribution("cte")
        self.assertEqual(self.company.nfe_dfe_next_query, next_query)

    # ── DF-e banner mock controls ───────────────────────────────────────

    def _banner_data(self, user, fiscal_type="nfe"):
        return (
            self.env["res.company"]
            .with_user(user)
            .with_company(self.company)
            .dfe_get_banner_data(fiscal_type)
        )

    def _fiscal_user(self):
        return self.manager.copy(
            {
                "login": "dfe_mock_fiscal_user",
                "groups_id": [
                    (6, 0, [self.env.ref("l10n_br_fiscal.group_user").id]),
                ],
            }
        )

    def test_banner_shows_mock_controls_to_fiscal_manager(self):
        data = self._banner_data(self.manager)
        self.assertTrue(data["mock_available"])
        self.assertTrue(data["mock_mode"])
        self.company.sudo().write({"dfe_mock_mode": False})
        self.assertFalse(self._banner_data(self.manager)["mock_mode"])

    def test_banner_hides_mock_controls_from_fiscal_user(self):
        data = self._banner_data(self._fiscal_user())
        self.assertFalse(data["mock_available"])

    def test_banner_hides_mock_controls_for_other_fiscal_type(self):
        # Only the NF-e pool is mocked, so no other service gets the controls.
        data = self._banner_data(self.manager, fiscal_type="cte")
        self.assertFalse(data["mock_available"])

    def _call(self, method):
        # The banner buttons call these on res.company with no record and no
        # argument, acting on the active company of the user.
        Company = (
            self.env["res.company"].with_user(self.manager).with_company(self.company)
        )
        return getattr(Company, method)()

    def test_button_toggle_mock_mode(self):
        result = self._call("action_toggle_dfe_mock_mode")
        self.assertFalse(self.company.dfe_mock_mode)
        self.assertEqual(result["tag"], "display_notification")
        self._call("action_toggle_dfe_mock_mode")
        self.assertTrue(self.company.dfe_mock_mode)

    def test_banner_search_all_uses_mock_pool(self):
        self.company.sudo().write({"nfe_dfe_next_query": False})
        self.env["dfe.mock.generate.wizard"].create(
            {"company_id": self.company.id, "quantity": 2, "generate_proc_nfe": False}
        ).action_generate()
        pool = self.env["dfe.mock.nsu"].search([("company_id", "=", self.company.id)])
        self.env["res.company"].with_company(self.company).dfe_action_search_all("nfe")
        self.assertTrue(all(pool.mapped("consumed")))
        documents = self.env["l10n_br_fiscal_dfe.document"].search(
            [
                ("company_id", "=", self.company.id),
                ("access_key", "in", pool.mapped("access_key")),
            ]
        )
        self.assertEqual(len(documents), 2)

    def test_mock_controls_require_fiscal_manager(self):
        Company = (
            self.env["res.company"]
            .with_user(self._fiscal_user())
            .with_company(self.company)
        )
        with self.assertRaises(AccessError):
            Company.action_toggle_dfe_mock_mode()
        self.assertTrue(self.company.dfe_mock_mode)

    # ── generated XML ───────────────────────────────────────────────────

    def test_generated_xml_escapes_names(self):
        self.company.name = "Empresa <Mock> & Cia"
        wizard = self.env["dfe.mock.generate.wizard"].create(
            {"company_id": self.company.id}
        )
        partner_data = {
            "cnpj": "10588201000105",
            "name": "A & B Ltda",
            "uf_code": "35",
            "ie": "ISENTO",
        }
        emission_dt = datetime(2026, 2, 1, 10, 0, 0)
        ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

        res_xml = etree.fromstring(
            wizard._build_res_nfe_xml(ACCESS_KEY, partner_data, 10.0, emission_dt)
        )
        self.assertEqual(res_xml.findtext("nfe:xNome", namespaces=ns), "A & B Ltda")

        proc_xml = etree.fromstring(
            wizard._build_proc_nfe_xml(ACCESS_KEY, partner_data, 10.0, emission_dt)
        )
        self.assertEqual(
            proc_xml.findtext(".//nfe:emit/nfe:xNome", namespaces=ns), "A & B Ltda"
        )
        self.assertEqual(
            proc_xml.findtext(".//nfe:dest/nfe:xNome", namespaces=ns),
            "Empresa <Mock> & Cia",
        )

    def test_xml_pretty_indents_for_display_only(self):
        record = self._create_nsu("000000000000099")
        self.assertEqual(record.xml_content, SAMPLE_RES_NFE)
        self.assertNotIn("\n", record.xml_content)
        self.assertIn("\n", record.xml_pretty)
        self.assertIn("<chNFe", record.xml_pretty)
        record.xml_content = "not xml"
        self.assertEqual(record.xml_pretty, "not xml")
        record.xml_content = "<resNFe"
        self.assertEqual(record.xml_pretty, "<resNFe")
        arch = self.env["dfe.mock.nsu"].get_view(view_type="form")["arch"]
        pretty = arch[arch.index('name="xml_pretty"') :]
        self.assertIn('widget="ace"', pretty)
        self.assertLess(pretty.index('widget="ace"'), pretty.index('readonly="1"'))
