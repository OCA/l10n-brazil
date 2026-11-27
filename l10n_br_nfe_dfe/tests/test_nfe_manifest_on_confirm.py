# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import re
from datetime import timedelta
from types import SimpleNamespace
from unittest import mock

from odoo import fields

from odoo.addons import l10n_br_nfe
from odoo.addons.l10n_br_fiscal_edi.tests.common import KEY_1, KEY_3, EdiImportCase
from odoo.addons.queue_job.tests.common import trap_jobs


def _processor():
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
    return SimpleNamespace(
        ciencia_da_operacao=lambda key, cnpj: answer,
        confirmacao_da_operacao=lambda key, cnpj: answer,
    )


class TestNfeManifestOnConfirm(EdiImportCase):
    """The manifestation that the company chose, registered when an NF-e received
    from a supplier is confirmed."""

    def _document(self, days=2, **values):
        document = self._create_imported_document(
            review=False,
            document_key=KEY_1,
            document_date=fields.Datetime.now() - timedelta(days=days),
            **values,
        )
        document.authorization_date = document.document_date
        return document

    def _confirm(self, document, option):
        document.company_id.sudo().nfe_manifest_on_document_confirm = option
        with trap_jobs() as trap:
            document.action_document_confirm()
        return trap

    def _perform(self, trap):
        with mock.patch.object(
            type(self.env["l10n_br_nfe.md_event"]),
            "_get_processor",
            return_value=_processor(),
        ):
            trap.perform_enqueued_jobs()

    def _events(self):
        return self.env["l10n_br_nfe.md_event"].search([("access_key", "=", KEY_1)])

    def test_nothing_is_registered_by_default(self):
        trap = self._confirm(self._document(), "none")

        trap.assert_jobs_count(0)
        self.assertEqual(self.company.nfe_manifest_on_document_confirm, "none")

    def test_the_acknowledgement_is_registered_by_a_job_when_confirming(self):
        document = self._document(days=2)

        trap = self._confirm(document, "ciencia")

        trap.assert_jobs_count(1)
        self.assertFalse(self._events())
        self._perform(trap)
        self.assertEqual(self._events().event_type, "ciente")
        self.assertEqual(self._events().state, "done")

    def test_the_acknowledgement_is_skipped_with_a_notice_after_ten_days(self):
        document = self._document(days=11)

        trap = self._confirm(document, "ciencia")

        trap.assert_jobs_count(0)
        self.assertEqual(document.state_edoc, "autorizada")
        self.assertIn("10 days", "".join(document.message_ids.mapped("body")))

    def test_the_confirmation_is_registered_even_after_ten_days(self):
        document = self._document(days=40)

        trap = self._confirm(document, "confirmacao")

        trap.assert_jobs_count(1)
        self._perform(trap)
        self.assertEqual(self._events().event_type, "confirmado")

    def test_a_manifestation_already_registered_is_not_repeated(self):
        document = self._document()
        self.env["l10n_br_nfe.md_event"].create(
            {
                "access_key": KEY_1,
                "event_type": "ciente",
                "state": "done",
                "company_id": self.company.id,
            }
        )

        trap = self._confirm(document, "ciencia")

        trap.assert_jobs_count(0)

    def test_a_document_that_was_not_imported_is_not_manifested(self):
        document = self._document()
        document.imported_document = False

        trap = self._confirm(document, "confirmacao")

        trap.assert_jobs_count(0)

    def _user(self, login, nfe):
        user = self._fiscal_user(login)
        user.email = f"{login}@example.com"
        if nfe:
            user.groups_id = [(4, self.env.ref("l10n_br_nfe.group_user").id)]
        return user

    def test_the_event_of_an_nfe_user_is_registered_by_the_job(self):
        user = self._user("manifest_nfe", nfe=True)
        document = (
            self._document()
            .with_user(user)
            .with_context(allowed_company_ids=self.company.ids)
        )

        trap = self._confirm(document, "confirmacao")
        self._perform(trap)

        self.assertEqual(self._events().state, "done")
        self.assertEqual(self._events().create_uid, user)

    def test_a_common_fiscal_user_confirms_without_the_manifestation(self):
        user = self._user("manifest_fiscal", nfe=False)
        document = (
            self._document()
            .with_user(user)
            .with_context(allowed_company_ids=self.company.ids)
        )

        trap = self._confirm(document, "confirmacao")

        trap.assert_jobs_count(0)
        self.assertEqual(document.state_edoc, "autorizada")
        self.assertFalse(self._events())
        self.assertIn("permission of NF-e user", document.message_ids[0].body)

    def test_a_note_the_company_issued_elsewhere_is_never_manifested(self):
        """The XML is a real NF-e whose issuer is the company: it enters as an
        authorized sale and no manifestation is registered."""
        path = os.path.join(
            l10n_br_nfe.__path__[0],
            "tests",
            "nfe",
            "v4_00",
            "leiauteNFe",
            f"NFe{KEY_3}.xml",
        )
        with open(path, "rb") as xml_file:
            xml = xml_file.read()
        key = "35200159594315000157550010000000992062777167"
        xml = xml.replace(KEY_3.encode(), key.encode()).replace(
            b"<nNF>3</nNF>", b"<nNF>99</nNF>"
        )
        xml = re.sub(
            rb"(<dest>\s*)<CNPJ>\d+</CNPJ>", rb"\1<CNPJ>11444777000161</CNPJ>", xml
        )
        # the file as the authority returns it: a note the company issued is confirmed
        # as authorized only with the protocol
        body = xml.decode().split("?>", 1)[1].strip()
        protocol = (
            '<protNFe versao="4.00"><infProt><tpAmb>2</tpAmb><verAplic>SVRS</verAplic>'
            f"<chNFe>{key}</chNFe><dhRecbto>2026-06-10T10:15:00-03:00</dhRecbto>"
            "<nProt>135200000000099</nProt><digVal>abc=</digVal><cStat>100</cStat>"
            "<xMotivo>Autorizado o uso da NF-e</xMotivo></infProt></protNFe>"
        )
        xml = (
            '<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
            f"{body.replace('</NFe>', '</NFe>' + protocol)}</nfeProc>"
        ).encode()
        company = self.env.ref("l10n_br_base.empresa_lucro_presumido")
        company.nfe_manifest_on_document_confirm = "confirmacao"
        documents, errors, _warnings = self.Document._edi_import_files(
            [("own.xml", xml)]
        )
        self.assertFalse(errors)
        document = documents
        product = self.env["product.product"].create({"name": "Own product"})
        document.fiscal_line_ids.product_id = product
        document.fiscal_line_ids.action_resolve_line()

        with trap_jobs() as trap:
            document.action_document_confirm()

        self.assertEqual(document.issuer, "company")
        self.assertEqual(document.state_edoc, "autorizada")
        trap.assert_jobs_count(0)
