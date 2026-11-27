# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
from unittest import mock

from odoo import Command
from odoo.tests import TransactionCase, tagged

from odoo.addons import l10n_br_nfe

OWN_FILE = "NFe35200681583054000129550010000000012760018057-nf-e.xml"
OWN_KEY = "35200681583054000129550010000000042760018059"
COLLECTION = (
    b"<cobr>"
    b"<dup><nDup>001</nDup><dVenc>2026-07-10</dVenc><vDup>2000.00</vDup></dup>"
    b"<dup><nDup>002</nDup><dVenc>2026-08-10</dVenc><vDup>2147.25</vDup></dup>"
    b"</cobr><pag>"
)
DUE_ACCOUNT_TYPES = ("asset_receivable", "liability_payable")


@tagged("post_install", "-at_install")
class TestOwnNoteInvoice(TransactionCase):
    """A note the company issued in another system, imported, confirmed and
    invoiced: the invoice is the customer one and the document is left alone."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.user = cls.env["res.users"].create(
            {
                "name": "Own note accountant",
                "login": "own_note_accountant",
                "groups_id": [
                    Command.set(cls.env.user.groups_id.ids),
                    Command.link(cls.env.ref("account.group_account_manager").id),
                    Command.link(cls.env.ref("l10n_br_fiscal.group_user").id),
                ],
            }
        )
        cls.user.partner_id.email = "own-note@test.com"
        cls.user.write(
            {
                "company_ids": [Command.set(cls.env["res.company"].search([]).ids)],
                "company_id": cls.company.id,
            }
        )
        cls.env = cls.env(
            user=cls.user,
            context=dict(
                cls.env.context,
                tracking_disable=True,
                allowed_company_ids=cls.company.ids,
            ),
        )
        cls.Document = cls.env["l10n_br_fiscal.document"]
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_venda")

    def _own_xml(self):
        path = os.path.join(
            l10n_br_nfe.__path__[0], "tests", "nfe", "v4_00", "leiauteNFe", OWN_FILE
        )
        with open(path, "rb") as xml_file:
            xml = xml_file.read()
        xml = xml.replace(OWN_FILE[3:47].encode(), OWN_KEY.encode())
        xml = xml.replace(b"<nNF>1</nNF>", b"<nNF>4</nNF>")
        xml = xml.replace(b"81493979000189", b"84148732000113")
        xml = xml.replace(b"E-COM07", b"ZZ-OWN-1").replace(b"FURN_8855", b"ZZ-OWN-2")
        xml = xml.replace(b"<pag>", COLLECTION, 1)
        # the file as the authority returns it: a note the company issued is confirmed
        # as authorized only with the protocol
        body = xml.decode().split("?>", 1)[1].strip()
        protocol = (
            '<protNFe versao="4.00"><infProt><tpAmb>2</tpAmb><verAplic>SVRS</verAplic>'
            f"<chNFe>{OWN_KEY}</chNFe><dhRecbto>2026-06-10T10:15:00-03:00</dhRecbto>"
            "<nProt>135200000000004</nProt><digVal>abc=</digVal><cStat>100</cStat>"
            "<xMotivo>Autorizado o uso da NF-e</xMotivo></infProt></protNFe>"
        )
        return (
            '<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
            f"{body.replace('</NFe>', '</NFe>' + protocol)}</nfeProc>"
        ).encode()

    def _confirmed_document(self, xml):
        documents, errors, _warnings = self.Document._edi_import_files(
            [("own.xml", xml)]
        )
        self.assertFalse(errors)
        document = documents
        for line in document.fiscal_line_ids:
            line._apply_import_depara(
                product=self.env["product.product"].create({"name": line.name}),
                uom=self.env["uom.uom"]._match_by_fiscal_code(line.partner_uom_code),
                fiscal_operation=self.operation,
            )
        document.fiscal_operation_id = self.operation
        document.action_document_confirm()
        return document

    def test_the_invoice_of_an_own_note_is_the_customer_one_and_leaves_the_document(
        self,
    ):
        xml = self._own_xml()
        model = type(self.Document)
        send_patch = mock.patch.object(model, "action_document_send", autospec=True)
        export_patch = mock.patch.object(model, "_document_export", autospec=True)
        send = send_patch.start()
        export = export_patch.start()
        self.addCleanup(send_patch.stop)
        self.addCleanup(export_patch.stop)
        document = self._confirmed_document(xml)
        self.assertEqual(document.state_edoc, "autorizada")
        self.assertEqual(document.issuer, "company")
        sequences = self.env["ir.sequence"].search([])
        numbers = sequences.mapped("number_next_actual")
        tags = (document.nfe40_dup.ids, document.nfe40_detPag.ids)
        supplierinfos = self.env["product.supplierinfo"].search_count([])

        with (
            mock.patch.object(
                model, "_edi_set_installments", autospec=True
            ) as set_installments,
            mock.patch.object(
                model, "_edi_set_payments", autospec=True
            ) as set_payments,
        ):
            action = document.action_generate_invoice()
            move = self.env["account.move"].browse(action["res_id"])
            self.assertEqual(move.move_type, "out_invoice")
            due_lines = move.line_ids.filtered(
                lambda line: line.account_id.account_type in DUE_ACCOUNT_TYPES
            ).sorted("date_maturity")
            self.assertEqual(
                [line.date_maturity.isoformat() for line in due_lines],
                ["2026-07-10", "2026-08-10"],
            )
            self.assertEqual(due_lines.mapped("debit"), [2000.0, 2147.25])
            self.assertEqual(due_lines.account_id.account_type, "asset_receivable")
            move.action_post()

        self.assertEqual(move.state, "posted")
        set_installments.assert_not_called()
        set_payments.assert_not_called()
        send.assert_not_called()
        export.assert_not_called()
        self.assertEqual((document.nfe40_dup.ids, document.nfe40_detPag.ids), tags)
        self.assertEqual(document.state_edoc, "autorizada")
        self.assertEqual(document.original_xml_file_id.raw, xml)
        self.assertEqual(
            (document.document_number, document.document_serie), ("4", "1")
        )
        self.assertEqual(sequences.mapped("number_next_actual"), numbers)
        self.assertEqual(
            self.env["product.supplierinfo"].search_count([]), supplierinfos
        )
        self.assertFalse(move.edi_payment_summary)

    def _without_series(self):
        series = self.env["l10n_br_fiscal.document.serie"].search(
            [
                (
                    "document_type_id",
                    "=",
                    self.env.ref("l10n_br_fiscal.document_55").id,
                ),
                ("company_id", "=", self.company.id),
            ]
        )
        series.sudo().active = False

    def test_an_own_note_without_a_serie_record_is_confirmed_and_invoiced(self):
        self._without_series()
        xml = self._own_xml()
        sequences = self.env["ir.sequence"].search([])
        numbers = sequences.mapped("number_next_actual")

        document = self._confirmed_document(xml)
        self.assertFalse(document.document_serie_id)
        move = self.env["account.move"].browse(
            document.action_generate_invoice()["res_id"]
        )
        move.action_post()

        self.assertEqual(move.move_type, "out_invoice")
        self.assertEqual(
            (document.document_number, document.document_serie), ("4", "1")
        )
        self.assertEqual(document.original_xml_file_id.raw, xml)
        self.assertEqual(sequences.mapped("number_next_actual"), numbers)

    def test_the_danfe_of_the_invoice_and_the_one_of_the_document_do_not_clash(self):
        document = self._confirmed_document(self._own_xml())
        move = self.env["account.move"].browse(
            document.action_generate_invoice()["res_id"]
        )
        move.action_post()
        report = self.env["ir.actions.report"]

        invoice_pdf, _kind = report._render_qweb_pdf(
            "main_template_danfe_account", move.ids
        )
        document_pdf, _kind = report._render_qweb_pdf(
            "main_template_danfe", document.ids
        )

        self.assertTrue(invoice_pdf.startswith(b"%PDF"))
        self.assertTrue(document_pdf.startswith(b"%PDF"))

        # the PDF of the document is kept on the document the first time it is
        # made and is the same at every view, whatever was printed from the invoice
        pdf = document.file_report_id
        self.assertTrue(pdf)
        document.with_context(bin_size=True).view_pdf()
        self.assertEqual(document.file_report_id, pdf)
        content = pdf.with_context(bin_size=False).raw
        report._render_qweb_pdf("main_template_danfe_account", move.ids)
        document.with_context(bin_size=True).view_pdf()
        self.assertEqual(document.file_report_id, pdf)
        self.assertEqual(pdf.with_context(bin_size=False).raw, content)
