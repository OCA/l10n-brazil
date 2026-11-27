# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from lxml import etree
from nfelib.nfse.bindings.v1_0.dps_v1_01 import Dps

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from ..constants.nfse_nacional import PROVEDOR_NFSE_NACIONAL
from .test_nfse_lifecycle import (
    AUTHORIZED,
    NFSE_KEY,
    REJECTED,
    SCHEMA_VALIDATION,
    SESSION_POST,
    SIGN_XML,
    mock_response,
)

NS = {"n": "http://www.sped.fazenda.gov.br/nfse"}
NEW_KEY = "42024042" + "1" + "6" * 41


@tagged("post_install", "-at_install")
class TestNfseReplace(TransactionCase):
    """Replacement of an authorized NFS-e by a DPS with the subst group."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.old = cls.env.ref(
            "l10n_br_nfse_nacional.demo_nfse_lc", raise_if_not_found=False
        )
        if not cls.old:
            return
        cls.old.company_id.write(
            {
                "processador_edoc": "oca",
                "provedor_nfse": PROVEDOR_NFSE_NACIONAL,
                "nfse_environment": "2",
            }
        )

    def setUp(self):
        super().setUp()
        if not self.old:
            self.skipTest("l10n_br_nfse_nacional demo data is not installed")
        patcher = mock.patch(SIGN_XML, return_value="<x>signed</x>")
        patcher.start()
        self.addCleanup(patcher.stop)
        with (
            self._valid_schema(),
            mock.patch(SESSION_POST, return_value=mock_response(AUTHORIZED)),
        ):
            self.old.action_document_confirm()
            self.old.action_document_send()
        self.assertEqual(self.old.state_edoc, "autorizada")

    def _valid_schema(self):
        # the mocked signature is not a DPS: only the unsigned one is validated here
        return mock.patch(SCHEMA_VALIDATION, return_value=[])

    def _replacement(self, **values):
        action = self.old.action_nfse_replace()
        new = self.env[action["res_model"]].browse(action["res_id"])
        self.assertTrue(new.fiscal_line_ids)
        self.assertEqual(new.company_id, self.old.company_id)
        self.assertEqual(new.partner_id, self.old.partner_id)
        self.assertEqual(
            new.fiscal_line_ids.mapped(lambda line: (line.quantity, line.price_unit)),
            self.old.fiscal_line_ids.mapped(
                lambda line: (line.quantity, line.price_unit)
            ),
        )
        new.write(values)
        return new

    def _confirmed_xml(self, new):
        with self._valid_schema():
            new.action_document_confirm()
        return new._serialize([])[0].to_xml()

    def _send(self, new, body, status=200):
        with self._valid_schema():
            new.action_document_confirm()
            with mock.patch(
                SESSION_POST, return_value=mock_response(body, status)
            ) as post:
                new.action_document_send()
        return post

    def test_replace_supported(self):
        self.assertTrue(self.old.nfse_replace_supported)

    def test_dps_without_replacement_has_no_subst(self):
        xml = self.old._serialize([])[0].to_xml()
        self.assertFalse(
            etree.fromstring(xml.encode()).xpath("//n:subst", namespaces=NS)
        )

    def test_dps_declares_the_replaced_nfse(self):
        new = self._replacement(
            nfse_replace_motive="03",
            nfse_replace_reason="Retroactive immunity for the service",
        )
        xml = self._confirmed_xml(new)
        self.assertEqual(Dps.schema_validation(xml), [])
        subst = etree.fromstring(xml.encode()).xpath("//n:subst", namespaces=NS)[0]
        self.assertEqual(subst.findtext("n:chSubstda", namespaces=NS), NFSE_KEY)
        self.assertEqual(subst.findtext("n:cMotivo", namespaces=NS), "03")
        self.assertEqual(
            subst.findtext("n:xMotivo", namespaces=NS),
            "Retroactive immunity for the service",
        )

    def test_dps_default_motive(self):
        new = self._replacement()
        xml = self._confirmed_xml(new)
        self.assertEqual(Dps.schema_validation(xml), [])
        subst = etree.fromstring(xml.encode()).xpath("//n:subst", namespaces=NS)[0]
        self.assertEqual(subst.findtext("n:cMotivo", namespaces=NS), "99")
        self.assertTrue(len(subst.findtext("n:xMotivo", namespaces=NS)) >= 15)

    def test_replace_authorized_marks_the_old_one_as_replaced(self):
        new = self._replacement()
        post = self._send(new, dict(AUTHORIZED, chaveAcesso=NEW_KEY, nNFSe="124"))
        self.assertEqual(new.state_edoc, "autorizada")
        self.assertEqual(new.nfse_key, NEW_KEY)
        self.assertEqual(self.old.state_edoc, "cancelada")
        self.assertIn(new.document_number, self.old.cancel_reason)
        self.assertTrue(self.old.cancel_event_id)
        # the ADN registers the replacement itself: only the DPS was posted
        self.assertEqual(post.call_count, 1)
        self.assertNotIn("/eventos", post.call_args[0][0])

    def test_replace_without_sent_xml_registers_the_event(self):
        new = self._replacement()
        new._nfse_mark_replaced("", "<NFSe/>")
        self.assertEqual(self.old.state_edoc, "cancelada")
        self.assertTrue(self.old.cancel_event_id.file_request_id)

    def test_replace_refuses_more_than_one_invoice(self):
        if "move_ids" not in self.old._fields:
            self.skipTest("l10n_br_account is not installed")
        moves = self.env["account.move"].browse([1, 2])
        with (
            mock.patch.object(type(self.old), "move_ids", moves),
            self.assertRaisesRegex(UserError, "more than one invoice"),
        ):
            self.old.action_nfse_replace()

    def test_replace_rejected_keeps_the_old_one(self):
        new = self._replacement()
        self._send(new, REJECTED, 400)
        self.assertEqual(new.state_edoc, "rejeitada")
        self.assertEqual(self.old.state_edoc, "autorizada")
        self.assertFalse(self.old.cancel_event_id)
