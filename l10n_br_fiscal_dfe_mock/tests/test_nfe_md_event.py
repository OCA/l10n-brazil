# Copyright 2026 Engenere (<https://engenere.one>)
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from unittest import mock

from odoo.tests.common import TransactionCase

from ..models.nfe_md_event import _build_mde_result, _MockMDeProcessor

# Sample resNFe XML matching the wizard's _build_res_nfe_xml output
SAMPLE_RES_NFE = (
    '<resNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00">'
    "<chNFe>35260210588201000105550010000001231000001230</chNFe>"
    "<CNPJ>10588201000105</CNPJ>"
    "<xNome>Partner Mock Ltda</xNome>"
    "<IE>111111111111</IE>"
    "<dhEmi>2026-01-15T10:30:00-03:00</dhEmi>"
    "<tpNF>1</tpNF>"
    "<vNF>5432.10</vNF>"
    "<digVal>mock+digest==</digVal>"
    "<dhRecbto>2026-01-15T10:30:00-03:00</dhRecbto>"
    "<cSitNFe>1</cSitNFe>"
    "</resNFe>"
)

ACCESS_KEY = "35260210588201000105550010000001231000001230"


class TestMockMDeProcessor(TransactionCase):
    """Tests for _MockMDeProcessor and _build_mde_result."""

    def test_build_mde_result_structure(self):
        result = _build_mde_result()
        self.assertEqual(result.retorno.status_code, 200)
        self.assertEqual(len(result.resposta.retEvento), 1)
        inf = result.resposta.retEvento[0].infEvento
        self.assertEqual(inf.cStat, "135")
        self.assertTrue(inf.nProt.startswith("MOCK"))
        self.assertIn("T", inf.dhRegEvento)

    def test_processor_ciencia(self):
        proc = _MockMDeProcessor()
        result = proc.ciencia_da_operacao("chave", "cnpj")
        self.assertEqual(result.resposta.retEvento[0].infEvento.cStat, "135")

    def test_processor_confirmacao(self):
        proc = _MockMDeProcessor()
        result = proc.confirmacao_da_operacao("chave", "cnpj")
        self.assertEqual(result.resposta.retEvento[0].infEvento.cStat, "135")

    def test_processor_desconhecimento(self):
        proc = _MockMDeProcessor()
        result = proc.desconhecimento_da_operacao("chave", "cnpj")
        self.assertEqual(result.resposta.retEvento[0].infEvento.cStat, "135")

    def test_processor_nao_realizada(self):
        proc = _MockMDeProcessor()
        result = proc.operacao_nao_realizada("chave", "cnpj")
        self.assertEqual(result.resposta.retEvento[0].infEvento.cStat, "135")


class TestNfeMdEventMock(TransactionCase):
    """Tests for the l10n_br_nfe.md_event mock overrides."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.company.sudo().write({"dfe_mock_mode": True})

        # Clean any pre-existing mock NSU data for this company
        cls.env["dfe.mock.nsu"].sudo().search(
            [("company_id", "=", cls.company.id)]
        ).unlink()

        cls.mde = cls.env["l10n_br_nfe.md_event"].create(
            {
                "company_id": cls.company.id,
                "access_key": ACCESS_KEY,
                "document_number": 123,
                "event_type": "ciente",
                "state": "draft",
            }
        )

    def setUp(self):
        super().setUp()
        # Clean mock NSU records before each test to avoid uniqueness conflicts
        self.env["dfe.mock.nsu"].sudo().search(
            [("company_id", "=", self.company.id)]
        ).unlink()
        # Reset MDE state
        self.mde.write({"event_type": "ciente", "state": "draft"})

    def _create_res_nfe_nsu(self, nsu="000000000000001", access_key=None):
        return self.env["dfe.mock.nsu"].create(
            {
                "nsu": nsu,
                "schema_type": "resNFe",
                "xml_content": SAMPLE_RES_NFE,
                "access_key": access_key or ACCESS_KEY,
                "company_id": self.company.id,
            }
        )

    # ── _get_processor ──────────────────────────────────────────────────

    def test_get_processor_mock_mode_on(self):
        processor = self.mde._get_processor()
        self.assertIsInstance(processor, _MockMDeProcessor)

    def test_get_processor_mock_mode_off(self):
        """When mock mode is off, _get_processor delegates to super."""
        self.company.sudo().write({"dfe_mock_mode": False})
        try:
            with mock.patch(
                "odoo.addons.l10n_br_nfe.models.nfe_md_event."
                "NfeRecipientManifestationEvent._get_processor"
            ) as patched_super:
                patched_super.return_value = "real_processor"
                result = self.mde._get_processor()
                self.assertEqual(result, "real_processor")
                patched_super.assert_called_once()
        finally:
            self.company.sudo().write({"dfe_mock_mode": True})

    # ── action_confirm — ciência generates procNFe ──────────────────────

    def test_action_confirm_ciencia_generates_proc_nfe(self):
        self._create_res_nfe_nsu()
        self.mde.action_confirm()

        self.assertEqual(self.mde.state, "done")

        proc_nfe = self.env["dfe.mock.nsu"].search(
            [
                ("company_id", "=", self.company.id),
                ("access_key", "=", ACCESS_KEY),
                ("schema_type", "=", "procNFe"),
            ]
        )
        self.assertEqual(len(proc_nfe), 1)
        self.assertIn("<nfeProc", proc_nfe.xml_content)
        self.assertFalse(proc_nfe.consumed)

    def test_action_confirm_confirmado_no_proc_nfe(self):
        """Non-ciência events should NOT generate procNFe."""
        self.mde.write({"event_type": "confirmado"})
        self.mde.action_confirm()

        proc_nfe = self.env["dfe.mock.nsu"].search(
            [
                ("company_id", "=", self.company.id),
                ("access_key", "=", ACCESS_KEY),
                ("schema_type", "=", "procNFe"),
            ]
        )
        self.assertFalse(proc_nfe)

    def test_action_confirm_desconhecido_no_proc_nfe(self):
        self.mde.write({"event_type": "desconhecido"})
        self.mde.action_confirm()

        proc_nfe = self.env["dfe.mock.nsu"].search(
            [
                ("company_id", "=", self.company.id),
                ("access_key", "=", ACCESS_KEY),
                ("schema_type", "=", "procNFe"),
            ]
        )
        self.assertFalse(proc_nfe)

    def test_action_confirm_nao_realizado_no_proc_nfe(self):
        self.mde.write({"event_type": "nao_realizado"})
        self.mde.action_confirm()

        proc_nfe = self.env["dfe.mock.nsu"].search(
            [
                ("company_id", "=", self.company.id),
                ("access_key", "=", ACCESS_KEY),
                ("schema_type", "=", "procNFe"),
            ]
        )
        self.assertFalse(proc_nfe)

    def test_action_confirm_mock_off_skips_generation(self):
        """When mock mode is off, action_confirm should NOT generate procNFe."""
        self._create_res_nfe_nsu()
        self.company.sudo().write({"dfe_mock_mode": False})
        try:
            # Mock _get_processor so it doesn't fail trying to reach SEFAZ
            with mock.patch.object(
                type(self.mde),
                "_get_processor",
                return_value=_MockMDeProcessor(),
            ):
                self.mde.action_confirm()

            proc_nfe = self.env["dfe.mock.nsu"].search(
                [
                    ("company_id", "=", self.company.id),
                    ("access_key", "=", ACCESS_KEY),
                    ("schema_type", "=", "procNFe"),
                ]
            )
            self.assertFalse(proc_nfe)
        finally:
            self.company.sudo().write({"dfe_mock_mode": True})

    # ── _mock_generate_proc_nfe edge cases ──────────────────────────────

    def test_generate_proc_nfe_already_exists(self):
        """If procNFe already exists for the key, skip creation."""
        self._create_res_nfe_nsu()
        self.env["dfe.mock.nsu"].create(
            {
                "nsu": "000000000000099",
                "schema_type": "procNFe",
                "xml_content": "<nfeProc>existing</nfeProc>",
                "access_key": ACCESS_KEY,
                "company_id": self.company.id,
            }
        )

        self.mde.action_confirm()

        proc_nfes = self.env["dfe.mock.nsu"].search(
            [
                ("company_id", "=", self.company.id),
                ("access_key", "=", ACCESS_KEY),
                ("schema_type", "=", "procNFe"),
            ]
        )
        # Should still be just the one we created manually
        self.assertEqual(len(proc_nfes), 1)
        self.assertEqual(proc_nfes.nsu, "000000000000099")

    def test_generate_proc_nfe_no_res_nfe(self):
        """If no resNFe exists for the key, skip creation gracefully."""
        # setUp already cleans all NSU records, so no resNFe exists
        self.mde.action_confirm()

        proc_nfe = self.env["dfe.mock.nsu"].search(
            [
                ("company_id", "=", self.company.id),
                ("access_key", "=", ACCESS_KEY),
                ("schema_type", "=", "procNFe"),
            ]
        )
        self.assertFalse(proc_nfe)

    # ── _mock_parse_res_nfe ─────────────────────────────────────────────

    def test_parse_res_nfe_extracts_fields(self):
        partner_data, amount, emission_dt = self.mde._mock_parse_res_nfe(SAMPLE_RES_NFE)
        self.assertEqual(partner_data["cnpj"], "10588201000105")
        self.assertEqual(partner_data["name"], "Partner Mock Ltda")
        self.assertEqual(partner_data["ie"], "111111111111")
        # UF code comes from access_key[:2]
        self.assertEqual(partner_data["uf_code"], ACCESS_KEY[:2])
        self.assertAlmostEqual(amount, 5432.10, places=2)
        self.assertEqual(emission_dt.year, 2026)
        self.assertEqual(emission_dt.month, 1)
        self.assertEqual(emission_dt.day, 15)

    def test_parse_res_nfe_defaults_on_missing_fields(self):
        """XML with minimal fields should use defaults."""
        minimal_xml = (
            '<resNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00">'
            "<chNFe>35260200000000000000550010000001231000001230</chNFe>"
            "</resNFe>"
        )
        partner_data, amount, emission_dt = self.mde._mock_parse_res_nfe(minimal_xml)
        self.assertEqual(partner_data["cnpj"], "")
        self.assertEqual(partner_data["name"], "Emitente Mock")
        self.assertEqual(partner_data["ie"], "ISENTO")
        self.assertAlmostEqual(amount, 1000.00, places=2)

    def test_parse_res_nfe_no_namespace(self):
        """XML without namespace should still be parsed."""
        bare_xml = (
            "<resNFe>"
            "<CNPJ>12345678000199</CNPJ>"
            "<xNome>Teste Sem NS</xNome>"
            "<IE>ISENTO</IE>"
            "<dhEmi>2026-02-01T08:00:00</dhEmi>"
            "<vNF>999.99</vNF>"
            "</resNFe>"
        )
        partner_data, amount, emission_dt = self.mde._mock_parse_res_nfe(bare_xml)
        self.assertEqual(partner_data["cnpj"], "12345678000199")
        self.assertEqual(partner_data["name"], "Teste Sem NS")
        self.assertAlmostEqual(amount, 999.99, places=2)
        self.assertEqual(emission_dt.month, 2)

    # ── NSU auto-increment ──────────────────────────────────────────────

    def test_proc_nfe_nsu_auto_increments(self):
        """Generated procNFe should get the next available NSU."""
        self._create_res_nfe_nsu(nsu="000000000000010")

        self.mde.action_confirm()

        proc_nfe = self.env["dfe.mock.nsu"].search(
            [
                ("company_id", "=", self.company.id),
                ("access_key", "=", ACCESS_KEY),
                ("schema_type", "=", "procNFe"),
            ]
        )
        self.assertTrue(proc_nfe)
        self.assertEqual(proc_nfe.nsu, "000000000000011")

    # ── procNFe XML content ─────────────────────────────────────────────

    def test_proc_nfe_xml_contains_access_key(self):
        self._create_res_nfe_nsu()
        self.mde.action_confirm()

        proc_nfe = self.env["dfe.mock.nsu"].search(
            [
                ("company_id", "=", self.company.id),
                ("access_key", "=", ACCESS_KEY),
                ("schema_type", "=", "procNFe"),
            ]
        )
        self.assertIn(ACCESS_KEY, proc_nfe.xml_content)
        self.assertIn("<emit>", proc_nfe.xml_content)
        self.assertIn("10588201000105", proc_nfe.xml_content)
