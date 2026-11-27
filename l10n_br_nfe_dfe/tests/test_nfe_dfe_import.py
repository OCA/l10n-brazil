# Copyright (C) 2023 - TODAY Felipe Zago - KMEE
# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import ast
import base64
import gzip
import os
import re
import zipfile
from datetime import timedelta
from io import BytesIO
from types import SimpleNamespace
from unittest import mock

from xsdata.formats.dataclass.transports import DefaultTransport

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase

from odoo.addons import l10n_br_nfe
from odoo.addons.l10n_br_fiscal_edi.tests.common import fiscal_user_group_ids

from .test_nfe_dfe import (
    response_sucesso_individual,
    response_sucesso_multiplos,
)

KEY_FIXTURE = "35200159594315000157550010000000012062777161"
KEY = "35200159594315000157550010000000992062777167"


def _distribution_response(recipient):
    """The DF-e response with the NF-e of ``KEY`` addressed to ``recipient``.

    The key is another one, because the module has a demo document with the key
    of the fixture."""

    def replace_recipient(match):
        xml = gzip.decompress(base64.b64decode(match.group(2)))
        xml = xml.replace(b"81493979000189", recipient.encode())
        xml = xml.replace(KEY_FIXTURE.encode(), KEY.encode())
        xml = xml.replace(b"<nNF>1</nNF>", b"<nNF>99</nNF>")
        return match.group(1) + base64.b64encode(gzip.compress(xml)).decode() + "</"

    return re.sub(
        r"(<docZip[^>]*>)([^<]+)</", replace_recipient, response_sucesso_individual
    ).encode()


def _acknowledgement_processor():
    event = SimpleNamespace(
        cStat="135",
        xMotivo="ok",
        nProt="1",
        dhRegEvento="2026-11-18T10:00:00-03:00",
    )
    answer = SimpleNamespace(
        retorno=SimpleNamespace(status_code=200, _content=b"<ok/>"),
        resposta=SimpleNamespace(retEvento=[SimpleNamespace(infEvento=event)]),
    )
    return SimpleNamespace(ciencia_da_operacao=lambda key, cnpj: answer)


def _bytes(string):
    return string.encode("utf-8") if isinstance(string, str) else string


class TestNFeDFe(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")

    def _search_dfe(self):
        return self.env["l10n_br_fiscal_dfe.dfe"].search(
            [("company_id", "=", self.company.id)]
        )

    @mock.patch.object(DefaultTransport, "post")
    def test_download_document_proc_nfe(self, _mock_post):
        _mock_post.return_value = _distribution_response(self._recipient())

        self.company.nfe_dfe_search_documents()
        dfe_docs = self.env["l10n_br_fiscal_dfe.document"].search(
            [("company_id", "=", self.company.id)]
        )

        access_key = KEY
        for doc in dfe_docs.with_context(allowed_company_ids=self.company.ids):
            action = doc.import_document()
            self.assertEqual(action["res_model"], "l10n_br_fiscal.document")

        self.assertEqual(len(self._search_dfe()), 1)
        fiscal_doc = self.env["l10n_br_fiscal.document"].search(
            [("document_key", "=", access_key)], limit=1
        )
        self.assertTrue(fiscal_doc, "Fiscal document should be created after import")
        self.assertTrue(fiscal_doc.imported_document)
        self.assertEqual(action["res_id"], fiscal_doc.id)
        self.assertEqual(_mock_post.call_count, 1)

        imported_dfe = dfe_docs.filtered(lambda d: d.access_key == access_key)
        self.assertEqual(imported_dfe.fiscal_document_id, fiscal_doc)

        # Nothing was billed yet, so the button opens the fiscal document.
        action = imported_dfe.action_view_imported_document()
        self.assertEqual(action["res_model"], "l10n_br_fiscal.document")
        self.assertEqual(action["res_id"], fiscal_doc.id)

    def _recipient(self):
        return self.company.partner_id.cnpj_cpf_stripped

    @mock.patch.object(DefaultTransport, "post")
    def test_search_dfe_success(self, _mock_post):
        _mock_post.return_value = _bytes(response_sucesso_multiplos)

        self.company.nfe_dfe_search_documents()
        dfe_records = self._search_dfe()
        self.assertTrue(dfe_records)

        dfe_sorted = dfe_records.sorted(lambda record: record.nsu or "")
        dfe1, dfe2 = dfe_sorted

        self.assertEqual(dfe1.company_id, self.company)
        self.assertEqual(
            dfe1.access_key, "31201010588201000105550010038421171838422178"
        )
        self.assertEqual(dfe1.document_type_dfe, "summary")
        self.assertEqual(dfe1.nsu, "000000000000200")
        self.assertEqual(
            dfe1.display_name,
            "31201010588201000105550010038421171838422178 - Summary",
        )
        self.assertEqual(dfe1.dfe_document_id.color_status, "blue")
        self.assertEqual(dfe1.dfe_document_id.emitter, "ZAP GRAFICA E EDITORA EIRELI")
        self.assertEqual(dfe1.dfe_document_id.vat, "10.588.201/0001-05")
        self.assertEqual(
            dfe1.dfe_document_id.display_name,
            "31201010588201000105550010038421171838422178",
        )
        self.assertEqual(
            dfe1.dfe_document_id.access_key,
            "31201010588201000105550010038421171838422178",
        )

        self.assertEqual(dfe2.company_id, self.company)
        self.assertEqual(
            dfe2.access_key, "35200159594315000157550010000000012062777161"
        )
        self.assertEqual(dfe2.document_type_dfe, "complete")
        self.assertEqual(dfe2.dfe_document_id.emitter, "TESTE - Simples Nacional")
        self.assertEqual(dfe2.dfe_document_id.document_amount, 14.0)
        self.assertEqual(dfe2.dfe_document_id.vat, "59.594.315/0001-57")
        self.assertEqual(
            dfe2.dfe_document_id.access_key,
            "35200159594315000157550010000000012062777161",
        )
        self.assertEqual(
            dfe2.display_name,
            "35200159594315000157550010000000012062777161 - Complete",
        )
        self.assertEqual(dfe2.dfe_document_id.color_status, "green")
        self.assertEqual(
            dfe2.dfe_document_id.display_name,
            "35200159594315000157550010000000012062777161",
        )

    @mock.patch.object(DefaultTransport, "post")
    def test_generate_danfe(self, _mock_post):
        _mock_post.return_value = _bytes(response_sucesso_individual)
        self.company.nfe_dfe_search_documents()
        dfe_record = self._search_dfe()[0]

        result = dfe_record.dfe_document_id.make_pdf()

        self.assertEqual(result["type"], "ir.actions.act_url")
        self.assertTrue(result["url"].startswith("/web/content/"))
        self.assertIn("download=true", result["url"])

    @mock.patch.object(DefaultTransport, "post")
    def test_download_documents(self, _mock_post):
        _mock_post.return_value = _bytes(response_sucesso_multiplos)

        self.company.nfe_dfe_search_documents()
        dfe_sorted = self._search_dfe().sorted(lambda record: record.nsu or "")
        dfe1, dfe2 = dfe_sorted

        attachment_2 = self.env["ir.attachment"].search(
            [("res_id", "=", dfe2.id), ("res_model", "=", "l10n_br_fiscal_dfe.dfe")]
        )
        self.assertTrue(attachment_2)

        result_dfe1 = dfe1.action_download_xml()
        attachment_single_dfe1 = self._get_attachment_from_result(result_dfe1)
        self.assertTrue(attachment_single_dfe1)
        self.assertEqual(attachment_single_dfe1, dfe1.attachment_id)

        result_dfe2_access_key = dfe2.dfe_document_id.action_download_xml()
        attachment_single_dfe2_access_key = self._get_attachment_from_result(
            result_dfe2_access_key
        )
        self.assertTrue(attachment_single_dfe2_access_key)
        with self.assertRaises(UserError):
            dfe1.dfe_document_id.action_download_xml()

    def _get_attachment_from_result(self, result):
        _, _, _, att_id, _ = result["url"].split("/")
        return self.env["ir.attachment"].browse(int(att_id))

    @mock.patch.object(DefaultTransport, "post")
    def test_download_xmls_zip_success(self, _mock_post):
        """Zip download with complete NF-e documents should return a valid zip."""
        _mock_post.return_value = _bytes(response_sucesso_multiplos)
        self.company.nfe_dfe_search_documents()

        dfe_docs = self.env["l10n_br_fiscal_dfe.document"].search(
            [("company_id", "=", self.company.id)]
        )
        # Filter only documents that have a complete DFe
        docs_with_complete = dfe_docs.filtered(
            lambda d: any(r.document_type_dfe == "complete" for r in d.dfe_ids)
        )
        self.assertTrue(docs_with_complete)

        result = docs_with_complete.action_download_xmls_zip()

        self.assertEqual(result["type"], "ir.actions.act_url")
        self.assertIn("download=true", result["url"])
        self.assertIn("dfe_xmls.zip", result["url"])

        # Verify zip content
        att_id = int(result["url"].split("/")[3])
        attachment = self.env["ir.attachment"].browse(att_id)
        zip_data = base64.b64decode(attachment.with_context(bin_size=False).datas)
        with zipfile.ZipFile(BytesIO(zip_data), "r") as zf:
            self.assertTrue(zf.namelist(), "Zip should contain at least one file")
            for name in zf.namelist():
                self.assertTrue(name.endswith(".xml"))

    @mock.patch.object(DefaultTransport, "post")
    def test_download_xmls_zip_no_complete(self, _mock_post):
        """Zip download with only summary documents should raise UserError."""
        _mock_post.return_value = _bytes(response_sucesso_multiplos)
        self.company.nfe_dfe_search_documents()

        dfe_docs = self.env["l10n_br_fiscal_dfe.document"].search(
            [("company_id", "=", self.company.id)]
        )
        # Keep only documents without complete DFe
        docs_summary_only = dfe_docs.filtered(
            lambda d: not any(r.document_type_dfe == "complete" for r in d.dfe_ids)
        )
        self.assertTrue(docs_summary_only, "Should have at least one summary-only doc")

        with self.assertRaises(UserError):
            docs_summary_only.action_download_xmls_zip()


class TestNFeDFeImportByKey(TransactionCase):
    """The key of a note that only has the summary: the acknowledgement that
    releases the XML, and the document that is created when the XML arrives."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.Wizard = cls.env["l10n_br_fiscal_edi.document.import.wizard"]
        cls.event_model = type(cls.env["l10n_br_nfe.md_event"])

    def _summary(self, days=0):
        dfe_document = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": KEY,
                "company_id": self.company.id,
                "fiscal_type": "nfe",
                "document_state": "1",
                "document_emission_date": fields.Datetime.now() - timedelta(days=days),
            }
        )
        self.env["l10n_br_fiscal_dfe.dfe"].create(
            {
                "access_key": KEY,
                "company_id": self.company.id,
                "fiscal_type": "nfe",
                "dfe_document_id": dfe_document.id,
                "document_type_dfe": "summary",
            }
        )
        return dfe_document

    def _imported(self):
        return self.env["l10n_br_fiscal.document"].search(
            [("document_key", "=", KEY), ("company_id", "=", self.company.id)]
        )

    def _acknowledge(self, wizard):
        with mock.patch.object(
            self.event_model,
            "_get_processor",
            return_value=_acknowledgement_processor(),
        ):
            return wizard.action_confirm_request()

    def _fiscal_user(self, email=True, nfe=True):
        groups = [
            self.env.ref("base.group_user").id,
            self.env.ref("l10n_br_fiscal.group_user").id,
        ]
        if nfe:
            groups.append(self.env.ref("l10n_br_nfe.group_user").id)
        return self.env["res.users"].create(
            {
                "name": "Fiscal importer",
                "login": "nfe_dfe_importer",
                "email": "nfe_dfe_importer@example.com" if email else False,
                "company_id": self.company.id,
                "company_ids": [Command.set(self.company.ids)],
                "groups_id": [Command.set(groups)],
            }
        )

    def test_the_button_of_the_imported_document_is_named_for_the_fiscal_document(
        self,
    ):
        user = self._fiscal_user()
        view = (
            self.env["l10n_br_fiscal_dfe.document"]
            .with_user(user)
            .get_view(
                self.env.ref(
                    "l10n_br_nfe_dfe.view_l10n_br_fiscal_dfe_document_form_nfe"
                ).id
            )
        )

        self.assertIn("Fiscal Document", view["arch"])
        self.assertNotIn("Invoice", view["arch"])

    def test_the_summary_asks_to_acknowledge_before_the_xml_is_requested(self):
        dfe_document = self._summary()

        action = dfe_document.import_document()

        wizard = self.Wizard.browse(action["res_id"])
        self.assertEqual(wizard.state, "confirm")
        self.assertIn("ciencia", wizard.confirm_message)
        self.assertFalse(dfe_document.manifestations_ids)
        self._acknowledge(wizard)
        self.assertEqual(dfe_document.manifestations_ids.event_type, "ciente")
        self.assertEqual(dfe_document.manifestations_ids.state, "done")
        self.assertEqual(dfe_document.import_requested_user_id, self.env.user)
        self.assertIn("Acknowledgement", dfe_document.message_ids[0].body)
        self.assertFalse(self._imported())

    @mock.patch.object(DefaultTransport, "post")
    def test_the_document_is_created_when_the_complete_xml_arrives(self, mock_post):
        user = self._fiscal_user()
        dfe_document = self._summary()
        dfe_document.import_requested_user_id = user
        mock_post.return_value = _distribution_response(
            self.company.partner_id.cnpj_cpf_stripped
        )

        self.company.nfe_dfe_search_documents()

        document = self._imported()
        self.assertTrue(document)
        self.assertEqual(document.create_uid, user)
        self.assertFalse(dfe_document.import_requested_user_id)
        self.assertEqual(document.activity_ids.user_id, user)

    def test_the_acknowledgement_after_ten_days_asks_for_the_file(self):
        dfe_document = self._summary(days=30)

        with self.assertRaisesRegex(UserError, "Upload the XML file"):
            dfe_document.import_document()

        self.assertFalse(dfe_document.manifestations_ids)

    def test_a_note_already_acknowledged_only_registers_the_request(self):
        dfe_document = self._summary()
        self.env["l10n_br_nfe.md_event"].create(
            {
                "access_key": KEY,
                "event_type": "ciente",
                "state": "done",
                "company_id": self.company.id,
                "dfe_document_id": dfe_document.id,
            }
        )

        action = dfe_document.import_document()

        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(len(dfe_document.manifestations_ids), 1)
        self.assertEqual(dfe_document.import_requested_user_id, self.env.user)

    def test_nfe_user_acknowledges_as_the_author(self):
        user = self._fiscal_user()
        dfe_document = self._summary()
        wizard = self.Wizard.with_user(user).browse(
            dfe_document.with_user(user).import_document()["res_id"]
        )

        self._acknowledge(wizard)

        self.assertEqual(dfe_document.manifestations_ids.create_uid, user)
        self.assertEqual(dfe_document.import_requested_user_id, user)

    def test_common_fiscal_user_is_refused_the_acknowledgement(self):
        user = self._fiscal_user(nfe=False)
        dfe_document = self._summary().with_user(user)

        with self.assertRaisesRegex(UserError, "permission of NF-e user"):
            dfe_document.import_document()
        with self.assertRaisesRegex(UserError, "permission of NF-e user"):
            dfe_document._dfe_import_request()

        self.assertFalse(dfe_document.sudo().manifestations_ids)
        self.assertFalse(dfe_document.sudo().import_requested_user_id)

    def test_a_note_already_acknowledged_needs_no_permission_to_request(self):
        user = self._fiscal_user(nfe=False)
        dfe_document = self._summary()
        self.env["l10n_br_nfe.md_event"].create(
            {
                "access_key": KEY,
                "event_type": "ciente",
                "state": "done",
                "company_id": self.company.id,
                "dfe_document_id": dfe_document.id,
            }
        )
        dfe_document.invalidate_recordset()

        dfe_document.with_user(user)._dfe_import_request()

        self.assertEqual(dfe_document.import_requested_user_id, user)

    def test_nfe_user_without_email_acknowledges(self):
        user = self._fiscal_user(email=False)
        dfe_document = self._summary()
        wizard = self.Wizard.with_user(user).browse(
            dfe_document.with_user(user).import_document()["res_id"]
        )

        self._acknowledge(wizard)

        self.assertEqual(dfe_document.manifestations_ids.state, "done")
        self.assertEqual(dfe_document.import_requested_user_id, user)
        self.assertIn("Acknowledgement", dfe_document.message_ids[0].body)


class TestNFeDFeInboxAction(TransactionCase):
    """The import from the inbox as the screen does it: the context of the action
    of the menu, the button of the record, and each profile."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.fiscal = cls._user("inbox_fiscal", ["l10n_br_fiscal.group_user"])
        cls.nfe_fiscal = cls._user(
            "inbox_nfe", ["l10n_br_fiscal.group_user", "l10n_br_nfe.group_user"]
        )
        cls.accountant = cls._user(
            "inbox_accountant", ["account.group_account_user", "l10n_br_nfe.group_user"]
        )

    @classmethod
    def _user(cls, login, groups):
        return cls.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "email": f"{login}@example.com",
                "company_id": cls.company.id,
                "company_ids": [Command.set(cls.company.ids)],
                "groups_id": [
                    Command.set(
                        [cls.env.ref("base.group_user").id]
                        + [cls.env.ref(group).id for group in groups]
                    )
                ],
            }
        )

    def _xml(self):
        path = os.path.join(
            l10n_br_nfe.__path__[0],
            "tests",
            "nfe",
            "v4_00",
            "leiauteNFe",
            f"NFe{KEY_FIXTURE}.xml",
        )
        with open(path, "rb") as xml_file:
            xml = xml_file.read()
        xml = re.sub(
            rb"(<dest>\s*)<(?:CNPJ|CPF)>\d+</(?:CNPJ|CPF)>",
            rb"\1<CNPJ>%s</CNPJ>" % self.company.partner_id.cnpj_cpf_stripped.encode(),
            xml,
        )
        xml = xml.replace(KEY_FIXTURE.encode(), KEY.encode())
        return xml.replace(b"<nNF>1</nNF>", b"<nNF>99</nNF>")

    def _record(self, complete):
        dfe_document = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": KEY,
                "company_id": self.company.id,
                "fiscal_type": "nfe",
                "document_state": "1",
            }
        )
        dfe = self.env["l10n_br_fiscal_dfe.dfe"].create(
            {
                "access_key": KEY,
                "company_id": self.company.id,
                "fiscal_type": "nfe",
                "dfe_document_id": dfe_document.id,
                "document_type_dfe": "complete" if complete else "summary",
            }
        )
        if complete:
            dfe.create_xml_attachment(self._xml())
        return dfe_document

    def _as(self, record, user, action_xmlid="l10n_br_nfe_dfe.action_nfe_dfe_document"):
        """The record with the context of the action of the menu, for the user."""
        action = self.env.ref(action_xmlid)
        context = dict(
            ast.literal_eval(action.context or "{}"),
            allowed_company_ids=self.company.ids,
        )
        return record.with_user(user).with_context(**context)

    def test_the_inbox_action_carries_the_default_that_used_to_break_the_import(self):
        action = self.env.ref("l10n_br_nfe_dfe.action_nfe_dfe_document")

        self.assertEqual(ast.literal_eval(action.context)["default_fiscal_type"], "nfe")

    def test_the_complete_record_is_imported_with_the_context_of_the_action(self):
        for label, user in (
            ("fiscal", self.fiscal),
            ("manager", self.env.ref("base.user_admin")),
        ):
            with self.subTest(profile=label):
                record = self._record(complete=True)

                action = self._as(record, user).import_document()

                document = self.env["l10n_br_fiscal.document"].browse(action["res_id"])
                self.assertEqual(document.document_key, KEY)
                self.assertNotEqual(document.fiscal_line_ids.fiscal_type, "nfe")
                self.assertEqual(document.create_uid, user)
                document.sudo().unlink()
                record.sudo().unlink()

    def test_the_accountant_without_the_fiscal_group_is_told_who_imports(self):
        record = self._record(complete=True)

        with self.assertRaisesRegex(UserError, "fiscal users"):
            self._as(record, self.accountant).import_document()

    def test_the_fiscal_user_sees_the_record_and_its_manifestations(self):
        record = self._record(complete=False)
        self.env["l10n_br_nfe.md_event"].create(
            {
                "access_key": KEY,
                "event_type": "ciente",
                "state": "done",
                "company_id": self.company.id,
                "dfe_document_id": record.id,
            }
        )

        as_fiscal = self._as(record, self.fiscal)

        Form(as_fiscal)
        self.assertEqual(as_fiscal.manifestation_status, "ciente")
        self.assertEqual(len(as_fiscal.manifestations_ids), 1)

    def test_the_summary_asks_the_nfe_user_to_confirm_the_acknowledgement(self):
        record = self._record(complete=False)

        action = self._as(record, self.nfe_fiscal).import_document()

        wizard = Form(
            self.env[action["res_model"]]
            .with_user(self.nfe_fiscal)
            .browse(action["res_id"])
        )
        self.assertEqual(wizard.state, "confirm")
        self.assertIn("ciencia", wizard.confirm_message)

    def test_the_summary_tells_the_common_fiscal_user_the_permission_is_missing(self):
        record = self._record(complete=False)

        with self.assertRaisesRegex(UserError, "permission of NF-e user"):
            self._as(record, self.fiscal).import_document()

        self.assertFalse(record.sudo().manifestations_ids)

    def test_the_key_typed_is_imported_by_the_fiscal_user_and_not_by_the_accountant(
        self,
    ):
        record = self._record(complete=True)

        for user, allowed in ((self.fiscal, True), (self.accountant, False)):
            with self.subTest(user=user.login):
                wizard = self.env["l10n_br_fiscal_edi.document.import.wizard"]
                wizard = wizard.with_user(user).with_context(
                    default_fiscal_type="nfe", allowed_company_ids=self.company.ids
                )
                if allowed:
                    action = wizard.create({"access_key": KEY}).action_import()
                    document = self.env["l10n_br_fiscal.document"].browse(
                        action["res_id"]
                    )
                    self.assertEqual(document.document_key, KEY)
                    document.sudo().unlink()
                else:
                    with self.assertRaises(AccessError):
                        wizard.create({"access_key": KEY})
        record.sudo().unlink()

    def test_the_other_inboxes_refuse_a_summary_with_a_message(self):
        for xmlid, fiscal_type in (
            ("l10n_br_cte_dfe.action_cte_dfe_document", "cte"),
            ("l10n_br_nfse_dfe.action_nfse_dfe_document", "nfse"),
        ):
            action = self.env.ref(xmlid, raise_if_not_found=False)
            if not action:
                continue
            with self.subTest(inbox=fiscal_type):
                record = self.env["l10n_br_fiscal_dfe.document"].create(
                    {
                        "access_key": "5" * 44,
                        "company_id": self.company.id,
                        "fiscal_type": fiscal_type,
                        "document_state": "1",
                    }
                )
                with self.assertRaises(UserError):
                    self._as(record, self.fiscal, xmlid).import_document()
                record.sudo().unlink()


class TestNFeDFeDemo(TransactionCase):
    """The two notes of the demo inbox: one imports, the other asks the ciencia."""

    def _record(self, xmlid):
        record = self.env.ref(f"l10n_br_nfe_dfe.{xmlid}", raise_if_not_found=False)
        if not record:
            self.skipTest("No demo data")
        company = record.company_id
        return record.with_context(allowed_company_ids=company.ids)

    def test_the_amount_of_the_demo_notes_is_in_the_currency_of_the_company(self):
        for xmlid in ("demo_dfe_document_complete", "demo_dfe_document_summary"):
            record = self._record(xmlid)
            self.assertEqual(record.currency_id, record.company_id.currency_id)

    def test_the_currency_of_a_note_follows_the_company_not_the_user(self):
        company = self.env["res.company"].create(
            {"name": "Other currency", "currency_id": self.env.ref("base.USD").id}
        )
        record = self.env["l10n_br_fiscal_dfe.document"].create(
            {"access_key": "9" * 44, "company_id": company.id}
        )

        self.assertEqual(record.currency_id, self.env.ref("base.USD"))
        self.assertEqual(record.company_id.currency_id, record.currency_id)

    def test_the_list_of_the_inbox_reads_the_amount_with_the_currency_of_the_company(
        self,
    ):
        record = self._record("demo_dfe_document_complete")
        user = self.env["res.users"].create(
            {
                "name": "Fiscal reader",
                "login": "nfe_dfe_reader",
                "company_id": record.company_id.id,
                "company_ids": [Command.set(record.company_id.ids)],
                "groups_id": [
                    Command.set(
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("l10n_br_fiscal.group_user").id,
                        ]
                    )
                ],
            }
        )
        data = record.with_user(user).read(["document_amount", "currency_id"])[0]

        self.assertEqual(data["currency_id"][0], record.company_id.currency_id.id)
        self.assertEqual(data["document_amount"], record.document_amount)

    def test_the_complete_note_of_the_inbox_is_imported_by_the_button(self):
        record = self._record("demo_dfe_document_complete")

        action = record.import_document()

        document = self.env["l10n_br_fiscal.document"].browse(action["res_id"])
        self.assertEqual(document.document_key, record.access_key)
        self.assertEqual(document.company_id, record.company_id)
        self.assertEqual(document.state_edoc, "em_digitacao")
        self.assertEqual(record.fiscal_document_id, document)

    def test_the_summary_of_the_inbox_asks_the_acknowledgement(self):
        record = self._record("demo_dfe_document_summary")

        action = record.import_document()

        wizard = self.env[action["res_model"]].browse(action["res_id"])
        self.assertEqual(wizard.state, "confirm")
        self.assertIn("ciencia", wizard.confirm_message)


@tagged("post_install", "-at_install")
class TestNFeDFeImportedDocumentAccess(TransactionCase):
    """Accounting is loaded after this module: the move exists only post install."""

    def _record(self, xmlid):
        record = self.env.ref(f"l10n_br_nfe_dfe.{xmlid}", raise_if_not_found=False)
        if not record:
            self.skipTest("No demo data")
        return record

    def test_a_pure_fiscal_user_opens_the_imported_document_from_the_inbox(self):
        record = self._record("demo_dfe_document_complete")
        user = self.env["res.users"].create(
            {
                "name": "Pure fiscal",
                "login": "nfe_dfe_pure_fiscal",
                "company_id": record.company_id.id,
                "company_ids": [Command.set(record.company_id.ids)],
                "groups_id": [
                    Command.set(fiscal_user_group_ids(self.env, form_groups=True))
                ],
            }
        )
        context = {"allowed_company_ids": record.company_id.ids}
        record = record.with_user(user).with_context(**context)
        record.import_document()
        if "move_ids" not in record.fiscal_document_id._fields:
            self.skipTest("No accounting")
        # An invoice of the import: accounting is not for a fiscal user.
        journal = (
            self.env["account.journal"]
            .sudo()
            .search(
                [("type", "=", "purchase"), ("company_id", "=", record.company_id.id)],
                limit=1,
            )
        )
        move = (
            self.env["account.move"]
            .sudo()
            .create(
                {
                    "move_type": "in_invoice",
                    "company_id": record.company_id.id,
                    # the journal of the company of the note, not the one by default
                    "journal_id": journal.id,
                    "partner_id": record.fiscal_document_id.partner_id.id,
                    "fiscal_document_id": record.fiscal_document_id.id,
                }
            )
        )
        self.assertEqual(record.fiscal_document_id.sudo().move_ids, move)
        self.env.flush_all()
        self.env.invalidate_all()

        action = record.action_view_imported_document()

        self.assertEqual(action["res_model"], "l10n_br_fiscal.document")
        document = (
            self.env[action["res_model"]]
            .with_user(user)
            .with_context(**action["context"])
            .browse(action["res_id"])
        )
        self.assertEqual(document, record.fiscal_document_id)
        view = document.get_view(view_type="form")
        names = [
            name
            for name in document._fields
            if 'name="%s"' % name in view["arch"] and name in document._fields
        ]
        self.assertTrue(names)
        document.read(names)
