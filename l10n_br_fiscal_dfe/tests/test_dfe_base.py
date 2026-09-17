# Copyright (C) 2023 - TODAY Felipe Zago - KMEE
# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=line-too-long

import base64
from unittest import mock

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal_dfe.tools import utils


class TestDfeBase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")

    def test_utils_format_nsu(self):
        self.assertEqual(utils.format_nsu("100"), "000000000000100")
        self.assertEqual(utils.format_nsu("0"), "000000000000000")
        self.assertEqual(utils.format_nsu(200), "000000000000200")
        self.assertFalse(utils.format_nsu(None))
        self.assertFalse(utils.format_nsu(""))
        self.assertFalse(utils.format_nsu("abc"))

    def test_utils_mask_cnpj(self):
        self.assertFalse(utils.mask_cnpj(False))
        self.assertEqual(utils.mask_cnpj("1234"), "1234")
        self.assertEqual(utils.mask_cnpj("31282204000196"), "31.282.204/0001-96")

    def test_document_partner_id_matching(self):
        # Use a unique, fake CNPJ for testing to avoid collision with existing data
        unique_cnpj_digits = "31282204000196"
        unique_cnpj_formatted = "31.282.204/0001-96"

        # 14-digit CNPJ embedded in the access key (positions 6-20)
        # Key format: 35(UF) + 20(Year) + 01(Month) + CNPJ + 55(Mod) + ...
        fake_key = f"352001{unique_cnpj_digits}5500100000000012062777161"

        doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": fake_key,
                "company_id": self.company.id,
                "fiscal_type": "nfe",
            }
        )

        partner = self.env["res.partner"].create(
            {
                "name": "Match Partner",
                "cnpj_cpf": unique_cnpj_formatted,
            }
        )

        # Force recompute
        doc._compute_partner_id()
        self.assertEqual(doc.partner_id, partner)

    def test_document_color_status(self):
        doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "35200199999999999999550010000000019999999991",
                "company_id": self.company.id,
                "fiscal_type": "nfe",
            }
        )
        self.assertFalse(doc.color_status)

        doc.document_state = "2"  # Cancelled
        doc._compute_color_status()
        self.assertEqual(doc.color_status, "muted")

    def test_xml_pretty_formatting(self):
        dfe = self.env["l10n_br_fiscal_dfe.dfe"].create(
            {
                "access_key": "35200199999999999999550010000000019999999991",
                "company_id": self.company.id,
                "document_type_dfe": "complete",
                "fiscal_type": "nfe",
            }
        )
        dfe.attachment_id = self.env["ir.attachment"].create(
            {
                "name": "test.xml",
                "datas": base64.b64encode(b"<xml><test>1</test></xml>"),
                "res_model": "l10n_br_fiscal_dfe.dfe",
                "res_id": dfe.id,
            }
        )
        self.assertTrue(dfe.xml_pretty)
        self.assertIn("test", dfe.xml_pretty)

    def test_dfe_log_with_string_and_bytes(self):
        result = mock.MagicMock()
        result.envio_xml = "<xml>request</xml>"
        result.retorno = None
        self.company._dfe_log("Test msg", result=result)

        log = self.env["l10n_br_fiscal_dfe.distribution_log"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        self.assertEqual(log.request_xml, "<xml>request</xml>")
        self.assertEqual(log.message, "Test msg")

    def test_dfe_validate_distribution_response(self):
        result = mock.MagicMock()
        result.resposta.cStat = "138"
        self.assertTrue(self.company._dfe_validate_distribution_response(result))

        result.resposta.cStat = "589"
        result.resposta.xMotivo = "Rejection Test"
        with self.assertRaises(ValidationError):
            self.company._dfe_validate_distribution_response(result, raise_message=True)
