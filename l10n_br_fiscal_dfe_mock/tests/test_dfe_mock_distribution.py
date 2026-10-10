# Copyright 2026 Engenere (<https://engenere.one>)
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import gzip
from unittest import mock

from odoo import fields
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

    # ── cooldown reset ──────────────────────────────────────────────────

    def test_reset_cooldown_clears_typed_field(self):
        self.company.sudo().write({"nfe_dfe_next_query": fields.Datetime.now()})
        self.company.with_company(self.company).action_reset_dfe_cooldown()
        self.assertFalse(self.company.nfe_dfe_next_query)

    # ── NF-e list header buttons ────────────────────────────────────────

    def _click(self, method):
        # Header buttons with display="always" run on an empty recordset
        # when no row is selected, in the active company of the user.
        Document = self.env["l10n_br_fiscal_dfe.document"]
        return getattr(
            Document.with_user(self.manager).with_company(self.company), method
        )()

    def _list_arch(self, user):
        view = self.env.ref("l10n_br_nfe_dfe.nfe_dfe_document_tree")
        Document = self.env["l10n_br_fiscal_dfe.document"].with_user(user)
        return Document.get_views([(view.id, "list")])["views"]["list"]["arch"]

    def test_header_buttons_only_for_fiscal_manager(self):
        buttons = (
            "action_dfe_mock_search_nfe",
            "action_dfe_mock_toggle",
            "action_dfe_mock_reset_cooldown",
        )
        arch = self._list_arch(self.manager)
        for button in buttons:
            self.assertIn(f'name="{button}"', arch)
        fiscal_user = self.manager.copy(
            {
                "login": "dfe_mock_fiscal_user",
                "groups_id": [
                    (6, 0, [self.env.ref("l10n_br_fiscal.group_user").id]),
                ],
            }
        )
        arch = self._list_arch(fiscal_user)
        for button in buttons:
            self.assertNotIn(f'name="{button}"', arch)

    def test_button_toggle_mock_mode(self):
        result = self._click("action_dfe_mock_toggle")
        self.assertFalse(self.company.dfe_mock_mode)
        self.assertEqual(result["tag"], "display_notification")
        self._click("action_dfe_mock_toggle")
        self.assertTrue(self.company.dfe_mock_mode)

    def test_button_reset_cooldown(self):
        self.company.sudo().write({"nfe_dfe_next_query": fields.Datetime.now()})
        result = self._click("action_dfe_mock_reset_cooldown")
        self.assertFalse(self.company.nfe_dfe_next_query)
        self.assertEqual(result["tag"], "display_notification")

    def test_button_query_nfe_uses_mock_pool(self):
        self.company.sudo().write({"nfe_dfe_next_query": False})
        self.env["dfe.mock.generate.wizard"].create(
            {"company_id": self.company.id, "quantity": 2, "generate_proc_nfe": False}
        ).action_generate()
        pool = self.env["dfe.mock.nsu"].search([("company_id", "=", self.company.id)])
        self._click("action_dfe_mock_search_nfe")
        self.assertTrue(all(pool.mapped("consumed")))
        documents = self.env["l10n_br_fiscal_dfe.document"].search(
            [
                ("company_id", "=", self.company.id),
                ("access_key", "in", pool.mapped("access_key")),
            ]
        )
        self.assertEqual(len(documents), 2)
