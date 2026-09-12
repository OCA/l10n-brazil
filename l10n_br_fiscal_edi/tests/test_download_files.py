# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestDownloadFiles(TransactionCase):
    """Handing the XML and the report of a selection over, unzipped.

    A download of the browser carries one file, so the server answers with the
    list of addresses and the client asks for them one at a time. What is
    tested here is the list: which files enter it, in which order, and what
    happens to the documents of the selection that have no file at all.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.document = cls._create_document()
        cls.xml = cls._create_attachment("nfe.xml")
        cls.sent = cls._create_attachment("sent.xml")
        cls.report = cls._create_attachment("danfe.pdf")
        # The two XML fields are related to the authorization event, so the way
        # to give a document its files is to give it the event.
        cls.document.authorization_event_id = cls._create_event(
            cls.document, cls.sent, cls.xml
        )
        cls.document.file_report_id = cls.report
        cls.empty = cls._create_document()

    @classmethod
    def _create_document(cls):
        return cls.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "document_serie_id": cls.env.ref(
                    "l10n_br_fiscal.document_55_serie_1"
                ).id,
                "fiscal_operation_type": "out",
            }
        )

    @classmethod
    def _create_attachment(cls, name):
        return cls.env["ir.attachment"].create({"name": name, "datas": b"MA=="})

    @classmethod
    def _create_event(cls, document, request, response):
        return cls.env["l10n_br_fiscal.event"].create(
            {
                "document_id": document.id,
                "document_type_id": document.document_type_id.id,
                "document_serie_id": document.document_serie_id.id,
                "document_number": "1",
                "company_id": document.company_id.id,
                "file_request_id": request.id,
                "file_response_id": response.id,
            }
        )

    def test_both_files_come_in_the_action(self):
        action = self.document.action_download_xml_and_report()
        self.assertEqual(action["type"], "ir.actions.client")
        self.assertEqual(action["tag"], "l10n_br_fiscal_edi.download_files")
        names = [each["name"] for each in action["params"]["files"]]
        self.assertEqual(names, ["nfe.xml", "danfe.pdf"])

    def test_each_button_brings_only_its_own_file(self):
        only_xml = self.document.action_download_xml()["params"]["files"]
        only_report = self.document.action_download_report()["params"]["files"]
        self.assertEqual([each["name"] for each in only_xml], ["nfe.xml"])
        self.assertEqual([each["name"] for each in only_report], ["danfe.pdf"])

    def test_the_url_asks_the_browser_to_download(self):
        files = self.document.action_download_xml()["params"]["files"]
        self.assertEqual(
            files[0]["url"],
            f"/web/content/{self.xml.id}/nfe.xml?download=true",
        )

    def test_the_sent_xml_serves_while_authorization_has_not_come(self):
        self.document.authorization_event_id.file_response_id = False
        files = self.document.action_download_xml()["params"]["files"]
        self.assertEqual([each["name"] for each in files], ["sent.xml"])

    def test_a_document_without_a_file_is_named_instead_of_refused(self):
        """A selection of many notes mixes the authorized with the ones in
        typing. Refusing the whole batch because of one is worse than handing
        over what exists and saying what was left out."""
        action = (self.document | self.empty).action_download_xml_and_report()
        self.assertEqual(len(action["params"]["files"]), 2)
        self.assertEqual(action["params"]["skipped"], self.empty.mapped("display_name"))

    def test_a_selection_with_no_file_at_all_is_refused(self):
        with self.assertRaises(UserError):
            self.empty.action_download_xml_and_report()
