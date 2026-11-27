# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
from unittest.mock import patch

import nfelib

from odoo.tests import Form

from odoo.addons.l10n_br_fiscal_edi.tests.common import EdiImportCase
from odoo.addons.l10n_br_mdfe.models.document_import import Document as MdfeReader
from odoo.addons.l10n_br_mdfe.models.res_city import ResCity
from odoo.addons.l10n_br_mdfe.models.res_company import ResCompany
from odoo.addons.l10n_br_mdfe.models.res_country_state import ResCountryState
from odoo.addons.l10n_br_mdfe.models.res_partner import ResPartner

MDFE_SAMPLE = os.path.join(
    os.path.dirname(nfelib.__file__),
    "mdfe",
    "samples",
    "v3_0",
    "50170876063965000276580010000011311421039568-mdfe.xml",
)
MDFE_KEY = "50170876063965000276580010000011311421039568"
MDFE_NAMESPACE = "http://www.portalfiscal.inf.br/mdfe"
SAMPLE_CNPJ = "00000000000000"
# CNPJ of the companies of the demo data
LUCRO_PRESUMIDO = "81583054000129"
LUCRO_REAL = "46312887000154"
PROTOCOL = (
    '<protMDFe versao="3.00"><infProt><tpAmb>2</tpAmb><verAplic>x</verAplic>'
    "<chMDFe>%(key)s</chMDFe><dhRecbto>2017-08-01T10:00:00-03:00</dhRecbto>"
    "<nProt>150170000000001</nProt><digVal>YWJj</digVal><cStat>%(status)s</cStat>"
    "<xMotivo>x</xMotivo></infProt></protMDFe>"
)


def mdfe_xml(emitter=LUCRO_PRESUMIDO, status=None):
    """The MDF-e that nfelib ships as a sample, issued by a company of the demo
    data; with ``status`` it comes as the ``mdfeProc`` that the authority returns."""
    with open(MDFE_SAMPLE, encoding="utf-8-sig") as handle:
        xml = handle.read()
    xml = xml.replace(f"<CNPJ>{SAMPLE_CNPJ}</CNPJ>", f"<CNPJ>{emitter}</CNPJ>", 1)
    # a municipality the demo data has, so that the unloading has a state
    xml = xml.replace("<cMunDescarga>0000000<", "<cMunDescarga>1200013<")
    if status:
        body = xml.split("?>", 1)[1].strip()
        xml = (
            f'<mdfeProc xmlns="{MDFE_NAMESPACE}" versao="3.00">{body}'
            + PROTOCOL % {"key": MDFE_KEY, "status": status}
            + "</mdfeProc>"
        )
    return xml.encode()


class TestMdfeDocumentImport(EdiImportCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.presumed = cls.env.ref("l10n_br_base.empresa_lucro_presumido")

    def _import(self, content, model=None):
        return (self.Document if model is None else model)._edi_import_files(
            [("mdfe.xml", content)]
        )

    def test_an_mdfe_of_the_company_becomes_a_document_it_issued(self):
        documents, errors, _warnings = self._import(mdfe_xml(status="100"))
        self.assertFalse(errors)
        self.assertEqual(documents.document_key, MDFE_KEY)
        self.assertEqual(documents.document_type_id.code, "58")
        self.assertEqual(documents.company_id, self.presumed)
        self.assertTrue(documents.imported_document)
        self.assertEqual(documents.issuer, "company")
        self.assertEqual(documents.fiscal_operation_type, "out")
        self.assertEqual(documents.document_number, "1131")
        self.assertFalse(documents.partner_id)
        self.assertTrue(documents.original_xml_file_id)

    def test_the_file_does_not_change_the_registry_of_the_company(self):
        names = (
            "name legal_name street_name street_number district zip state_id city_id "
            "l10n_br_ie_code l10n_br_im_code phone email"
        ).split()
        partner = self.presumed.partner_id
        partner.write(
            {
                "phone": "11 98888-0000",
                "email": "company@example.com",
                "l10n_br_im_code": "5555",
            }
        )

        def registry():
            partner.invalidate_recordset()
            return (self.presumed.name, [partner[name] for name in names])

        before = registry()
        documents, errors, _warnings = self._import(mdfe_xml(status="100"))
        self.assertFalse(errors)
        self.assertTrue(documents)
        documents.action_document_confirm()
        self.assertEqual(registry(), before)

    def test_confirming_an_mdfe_issued_by_the_company_does_not_send_it(self):
        sequences = (
            self.env["ir.sequence"].search([]).read(["id", "number_next_actual"])
        )
        documents, _errors, _warnings = self._import(mdfe_xml(status="100"))
        self.assertEqual(documents.fiscal_operation_type, "out")
        documents.action_document_confirm()
        self.assertEqual(documents.state_edoc, "autorizada")
        self.assertEqual(documents.document_number, "1131")
        self.assertFalse(documents.send_file_id)
        self.assertEqual(
            self.env["ir.sequence"].search([]).read(["id", "number_next_actual"]),
            sequences,
        )

    def test_the_damdfe_of_an_imported_mdfe_is_printed_from_the_original_xml(self):
        documents, _errors, _warnings = self._import(mdfe_xml(status="100"))
        documents.action_document_confirm()
        original = documents.original_xml_file_id.raw
        mails = self.env["mail.mail"].search_count([])
        self.assertFalse(documents.file_report_id)
        with patch(
            "odoo.addons.mail.models.mail_template.MailTemplate.send_mail"
        ) as send:
            action = documents.view_pdf()
        self.assertFalse(send.called)
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertTrue(documents.file_report_id.raw.startswith(b"%PDF"))
        self.assertEqual(documents.original_xml_file_id.raw, original)
        self.assertFalse(documents.authorization_file_id)
        self.assertEqual(self.env["mail.mail"].search_count([]), mails)

    def test_the_emitter_is_the_company_and_the_import_warns_of_nothing(self):
        documents, errors, _warnings = self._import(mdfe_xml(status="100"))
        self.assertFalse(errors)
        self.assertFalse(documents.import_partner_warning)

    def test_a_file_that_is_not_an_mdfe_is_left_to_the_next_reader(self):
        """Only this reader is called: what the others do with the file is theirs."""
        mro = type(self.Document).__mro__
        following = next(
            cls
            for cls in mro[mro.index(MdfeReader) + 1 :]
            if "_edi_import_read" in vars(cls)
        )
        cte = '<cteProc xmlns="http://www.portalfiscal.inf.br/cte"><CTe/></cteProc>'
        nfe = '<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe"><NFe/></nfeProc>'
        other_namespace = '<mdfeProc xmlns="http://example.com/other"/>'
        event = f'<eventoMDFe xmlns="{MDFE_NAMESPACE}"/>'
        with patch.object(following, "_edi_import_read", return_value="next"):
            for content in (cte, nfe, other_namespace, event, "not xml at all"):
                self.assertEqual(
                    MdfeReader._edi_import_read(
                        self.Document, "a.xml", content.encode()
                    ),
                    "next",
                )
            read = MdfeReader._edi_import_read(self.Document, "a.xml", mdfe_xml())
        self.assertEqual(read.reader, "mdfe")

    def test_the_overrides_of_the_mdfe_act_only_on_the_mdfe_schema(self):
        """The import dictionaries of another schema (NF-e, CT-e) go to the next
        override of the chain, never to the rules of the MDF-e."""
        cases = (
            (ResCity, "res.city", "match_or_create_m2o", ({"ibge_code": "1"}, {})),
            (
                ResCountryState,
                "res.country.state",
                "match_or_create_m2o",
                ({"code": "SP"}, {}),
            ),
            (ResCompany, "res.company", "_prepare_import_dict", ({"x": 1},)),
            (ResPartner, "res.partner", "_prepare_import_dict", ({"x": 1},)),
        )
        checked = 0
        for cls, model_name, method, args in cases:
            model = self.env[model_name].with_context(spec_schema="other")
            mro = type(model).__mro__
            following = next(
                (base for base in mro[mro.index(cls) + 1 :] if method in vars(base)),
                None,
            )
            if following is None:
                continue  # nothing of another schema can reach this override
            checked += 1
            with patch.object(following, method, return_value="next"):
                self.assertEqual(getattr(cls, method)(model, *args), "next", cls)
        self.assertGreaterEqual(checked, 2)

    def test_a_common_fiscal_user_opens_the_imported_mdfe(self):
        user = self._fiscal_user("fiscal_user_mdfe_form", self.presumed)
        model = self.Document.with_user(user).with_context(
            allowed_company_ids=self.presumed.ids
        )
        documents, errors, _warnings = self._import(mdfe_xml(status="100"), model)
        self.assertFalse(errors)
        with Form(documents.with_user(user)) as form:
            self.assertEqual(form.document_number, "1131")

    def test_the_company_is_the_issuer_of_the_mdfe(self):
        parsed = self.Document._edi_import_read("a.xml", mdfe_xml(emitter=LUCRO_REAL))
        self.assertEqual(parsed.company_vats, (("issuer", LUCRO_REAL),))
        self.assertEqual((parsed.reader, parsed.document_type_code), ("mdfe", "58"))
        self.assertEqual(parsed.issuer_vat, LUCRO_REAL)
        documents, errors, _warnings = self._import(mdfe_xml(emitter=LUCRO_REAL))
        self.assertFalse(errors)
        self.assertEqual(documents.company_id, self.other_company)

    def test_an_mdfe_of_another_issuer_is_refused(self):
        documents, errors, _warnings = self._import(mdfe_xml(emitter="12345678000195"))
        self.assertFalse(documents)
        self.assertIn("No company of this database", errors[0][1])

    def test_the_demo_mdfe_is_imported_as_authorized(self):
        document = self.Document.search(
            [("document_key", "=", "50170881583054000129580010000091311421039562")]
        )
        if not document:
            self.skipTest("the demo data is not installed")
        self.assertEqual(document.issuer, "company")
        self.assertEqual(document.state_edoc, "autorizada")
        self.assertTrue(document.imported_document)

    def test_the_status_comes_from_the_protocol_of_the_mdfe(self):
        for status, expected in (
            ("100", "authorized"),
            ("132", "authorized"),
            ("101", "cancelled"),
            ("999", "unknown"),
        ):
            parsed = self.Document._edi_import_read("a.xml", mdfe_xml(status=status))
            self.assertEqual((parsed.status, parsed.status_code), (expected, status))
        parsed = self.Document._edi_import_read("a.xml", mdfe_xml())
        self.assertEqual((parsed.status, parsed.status_code), ("unknown", ""))

    def test_an_mdfe_whose_protocol_does_not_authorize_it_is_refused(self):
        documents, errors, _warnings = self._import(mdfe_xml(status="999"))
        self.assertFalse(documents)
        self.assertIn("not authorized (status 999)", errors[0][1])

    def test_a_cancelled_mdfe_is_refused(self):
        documents, errors, _warnings = self._import(mdfe_xml(status="101"))
        self.assertFalse(documents)
        self.assertIn("cancelled", errors[0][1])

    def test_the_same_mdfe_twice_opens_the_same_document(self):
        documents, _errors, _warnings = self._import(mdfe_xml())
        again, errors, warnings = self._import(mdfe_xml())
        self.assertEqual(again, documents)
        self.assertFalse(errors)
        self.assertEqual(len(warnings), 1)

    def test_a_broken_mdfe_is_refused_as_invalid(self):
        for content in (
            f'<mdfeProc xmlns="{MDFE_NAMESPACE}"><MDFe/></mdfeProc>',
            f'<MDFe xmlns="{MDFE_NAMESPACE}"><infMDFe Id="MDFe123"/></MDFe>',
        ):
            documents, errors, _warnings = self._import(content.encode())
            self.assertFalse(documents)
            self.assertIn("not a valid MDF-e", errors[0][1])

    def test_a_common_fiscal_user_imports_an_mdfe(self):
        user = self._fiscal_user("fiscal_user_mdfe", self.presumed)
        model = self.Document.with_user(user).with_context(
            allowed_company_ids=self.presumed.ids
        )
        documents, errors, _warnings = self._import(mdfe_xml(status="100"), model)
        self.assertFalse(errors)
        self.assertEqual(documents.create_uid, user)
        self.assertEqual(documents.issuer, "company")
