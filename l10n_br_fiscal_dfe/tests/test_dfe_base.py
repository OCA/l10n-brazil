# Copyright (C) 2023 - TODAY Felipe Zago - KMEE
# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=line-too-long

import base64
from unittest import mock

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal_dfe.tools import utils


def _nfe_access_key(body):
    """43-digit NF-e key body plus the mod-11 check digit."""
    weights = [2, 3, 4, 5, 6, 7, 8, 9]
    total = 0
    for index, digit in enumerate(reversed(body)):
        total += int(digit) * weights[index % 8]
    rest = total % 11
    check = 0 if rest < 2 else 11 - rest
    return body + str(check)


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

        # 14-digit CNPJ embedded in the access key (positions 6-20).
        # The key must be exactly 44 digits: a national NFS-e uses 50, and
        # the partner match only reads the NF-e layout.
        # Key format: 35(UF) + 20(Year) + 01(Month) + CNPJ + 55(Mod) + ...
        fake_key = f"352001{unique_cnpj_digits}550010000000001206277716"

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
                "vat": unique_cnpj_formatted,
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

    def test_document_state_label_default_returns_raw_code(self):
        """Without a fiscal type specific override, the label is the raw code."""
        doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "35200199999999999999550010000000019999999992",
                "company_id": self.company.id,
                "fiscal_type": "cte",
                "document_state": "42",
            }
        )
        self.assertEqual(doc.document_state_label, "42")

    def test_utilization_stays_empty_when_the_source_cancels(self):
        """An authorized inbox row is available until the source voids it."""
        doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "35200199999999999999550010000000019999999993",
                "company_id": self.company.id,
                "fiscal_type": "nfe",
                "document_state": "1",
            }
        )
        self.assertEqual(doc.utilization, "available")

        doc.document_state = False
        self.assertEqual(doc.utilization, "available")

        doc.document_state = "3"
        self.assertFalse(doc.utilization)

        doc.document_state = "2"
        self.assertFalse(doc.utilization)

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

    def test_fiscal_document_link_follows_the_access_key(self):
        """An inbox row stays pending until a fiscal document has the same key."""
        access_key = _nfe_access_key("3524015959431500015755001000000001112345678")
        inbox = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": access_key,
                "company_id": self.company.id,
                "fiscal_type": "nfe",
            }
        )
        pending = self.env["l10n_br_fiscal_dfe.document"].search(
            [("id", "=", inbox.id), ("fiscal_document_id", "=", False)]
        )
        self.assertFalse(inbox.fiscal_document_id)
        self.assertEqual(pending, inbox)

        fiscal_document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "partner_id": self.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                "document_key": access_key,
            }
        )
        other_company = self.env.ref("l10n_br_base.empresa_simples_nacional")
        self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": other_company.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "partner_id": self.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                "document_key": access_key,
            }
        )
        inbox.invalidate_recordset()
        self.assertEqual(inbox.fiscal_document_id, fiscal_document)
        linked = self.env["l10n_br_fiscal_dfe.document"].search(
            [("id", "=", inbox.id), ("fiscal_document_id", "=", False)]
        )
        self.assertFalse(linked)

    def test_import_block_reason_follows_the_source_state(self):
        document = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "35200159594315000157550010000000012062777160",
                "company_id": self.company.id,
                "fiscal_type": "nfe",
                "document_state": "1",
            }
        )
        english = document.with_context(lang="en_US")
        self.assertFalse(english.import_block_reason)
        document.document_state = "3"
        self.assertEqual(
            english.import_block_reason,
            "This document was cancelled at the source.",
        )
        with self.assertRaises(UserError) as cancelled:
            english._check_import_allowed()
        self.assertEqual(
            str(cancelled.exception),
            "This document was cancelled at the source.",
        )
        document.document_state = "2"
        self.assertEqual(
            english.import_block_reason,
            "This document was denied at the source.",
        )
        document.document_state = "9"
        self.assertEqual(
            english.import_block_reason,
            "Only an authorized document can be imported.",
        )

    def test_a_complete_xml_without_a_source_state_is_blocked(self):
        access_key = _nfe_access_key("3520015959431500015755001000000008206277716")
        document = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": access_key,
                "company_id": self.company.id,
                "fiscal_type": "nfe",
            }
        )
        payload = self.env["l10n_br_fiscal_dfe.dfe"].create(
            {
                "dfe_document_id": document.id,
                "access_key": access_key,
                "company_id": self.company.id,
                "document_type_dfe": "complete",
                "fiscal_type": "nfe",
            }
        )
        payload.attachment_id = self.env["ir.attachment"].create(
            {
                "name": "complete.xml",
                "datas": base64.b64encode(b"<nfe/>"),
                "res_model": payload._name,
                "res_id": payload.id,
            }
        )
        self.assertEqual(
            document.with_context(lang="en_US").import_block_reason,
            "Only an authorized document can be imported.",
        )

    def test_an_authorized_document_uses_the_same_company_fiscal_document(self):
        access_key = _nfe_access_key("3520015959431500015755001000000009206277716")
        fiscal_document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "partner_id": self.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                "document_key": access_key,
            }
        )
        inbox = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": access_key,
                "company_id": self.company.id,
                "fiscal_type": "nfe",
                "document_state": "1",
            }
        )
        self.assertEqual(inbox._same_company_fiscal_document(), fiscal_document)
        self.assertFalse(inbox._get_import_invoice_block_reason())

    def test_a_row_without_an_access_key_has_no_fiscal_document(self):
        inbox = self.env["l10n_br_fiscal_dfe.document"].new(
            {
                "company_id": self.company.id,
                "fiscal_type": "nfe",
            }
        )
        self.assertFalse(inbox._same_company_fiscal_document())
