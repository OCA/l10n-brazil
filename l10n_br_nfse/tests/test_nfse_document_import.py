# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import re
from unittest.mock import patch

import nfelib
from erpbrasil.base.fiscal.cnpj_cpf import formata

from odoo.exceptions import UserError
from odoo.tests import Form

from odoo.addons.l10n_br_fiscal_edi.tests.common import EdiImportCase
from odoo.addons.l10n_br_nfse.models.document import Document as NfseDocument
from odoo.addons.l10n_br_nfse.models.document_import import Document as NfseReader

NFSE_SAMPLE = os.path.join(
    os.path.dirname(nfelib.__file__), "nfse", "samples", "v1_0", "nfse-ibscbs.xml"
)
SAMPLE_KEY = "42024042200000000000000000000000000126031234567892"
SAMPLE_CNPJ = "00000000000000"
# CNPJ of the partner and of the company of the demo data
PROVIDER = "59594315000157"
LUCRO_PRESUMIDO = "81583054000129"
LUCRO_REAL = "46312887000154"
UNKNOWN_PROVIDER = "12345678000195"
OTHER_UNKNOWN = "11444777000161"
WITHHOLDINGS = (
    "<tribFed><piscofins><CST>01</CST><vBCPisCofins>1000.00</vBCPisCofins>"
    "<pAliqPis>0.65</pAliqPis><pAliqCofins>3.00</pAliqCofins><vPis>6.50</vPis>"
    "<vCofins>30.00</vCofins><tpRetPisCofins>3</tpRetPisCofins></piscofins>"
    "<vRetIRRF>15.00</vRetIRRF><vRetCSLL>46.50</vRetCSLL></tribFed>"
)


def nfse_xml(taker=LUCRO_PRESUMIDO, provider=PROVIDER, withholdings=False):
    """The national NFS-e that nfelib ships as a sample, with the parties moved to
    the partners and the companies of the demo data.

    :param withholdings: PIS and COFINS withheld, and IRRF and CSLL as well
    """
    with open(NFSE_SAMPLE, encoding="utf-8") as handle:
        xml = handle.read()
    xml = re.sub(r"(<toma>\s*<CNPJ>)\d+", rf"\g<1>{taker}", xml)
    xml = xml.replace(f"<CNPJ>{SAMPLE_CNPJ}</CNPJ>", f"<CNPJ>{provider}</CNPJ>")
    if withholdings:
        xml = xml.replace("</tribMun>", f"</tribMun>{WITHHOLDINGS}", 1)
    return xml.encode()


class TestNfseDocumentImport(EdiImportCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.presumed = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        # the demo data sets the default service of this company
        cls.presumed.nfse_import_product_id = False
        cls.provider = cls.env["res.partner"].search(
            [("cnpj_cpf_stripped", "=", PROVIDER)], limit=1
        )

    def _import(self, content, model=None):
        return (self.Document if model is None else model)._edi_import_files(
            [("nfse.xml", content)]
        )

    def test_a_nfse_is_read_and_becomes_a_document_of_the_taker(self):
        documents, errors, _warnings = self._import(nfse_xml())
        self.assertFalse(errors)
        self.assertEqual(documents.document_key, SAMPLE_KEY)
        self.assertEqual(documents.document_type_id.code, "SE")
        self.assertEqual(documents.company_id, self.presumed)
        self.assertTrue(documents.imported_document)
        self.assertEqual(documents.issuer, "partner")
        self.assertEqual(documents.fiscal_operation_id.fiscal_operation_type, "in")
        self.assertEqual(documents.fiscal_operation_type, "in")
        self.assertEqual(documents.partner_id, self.provider)
        self.assertEqual(documents.document_serie, "00007")
        self.assertTrue(documents.original_xml_file_id)
        line = documents.fiscal_line_ids
        self.assertEqual(line.name, "Desenvolvimento de sistema sob encomenda")
        self.assertAlmostEqual(line.price_unit, 1000.0)
        self.assertAlmostEqual(line.issqn_value, 20.0)
        self.assertEqual(line.import_state, "pending")

    def test_the_incidence_city_of_the_file_survives_a_recompute(self):
        documents, _errors, _warnings = self._import(nfse_xml())
        line = documents.fiscal_line_ids
        city = line.issqn_fg_city_id
        self.assertEqual(city.ibge_code, "4202404")
        self.assertNotEqual(city, self.presumed.partner_id.city_id)
        line._compute_issqn_fg_city_id()
        self.assertEqual(line.issqn_fg_city_id, city)

    def _sequences(self):
        return self.env["ir.sequence"].search([]).read(["id", "number_next_actual"])

    def test_a_nfse_issued_by_the_company_becomes_an_outgoing_document(self):
        sequences = self._sequences()
        documents, errors, _warnings = self._import(
            nfse_xml(taker=UNKNOWN_PROVIDER, provider=LUCRO_PRESUMIDO),
        )
        self.assertFalse(errors)
        self.assertEqual(documents.company_id, self.presumed)
        self.assertEqual(documents.issuer, "company")
        self.assertEqual(documents.fiscal_operation_type, "out")
        self.assertEqual(documents.fiscal_operation_id.fiscal_operation_type, "out")
        self.assertEqual(documents.state_edoc, "em_digitacao")
        self.assertTrue(documents.imported_document)
        self.assertEqual(documents.partner_id.cnpj_cpf_stripped, UNKNOWN_PROVIDER)
        self.assertEqual(
            documents.partner_id.legal_name, "EMPRESA TOMADORA DE TESTE LTDA"
        )
        self.assertEqual(documents.document_key, SAMPLE_KEY)
        self.assertEqual(documents.document_number, "1")
        self.assertEqual(documents.document_serie, "00007")
        line = documents.fiscal_line_ids
        self.assertEqual(line.name, "Desenvolvimento de sistema sob encomenda")
        self.assertAlmostEqual(line.price_unit, 1000.0)
        self.assertAlmostEqual(line.issqn_value, 20.0)
        self.assertEqual(self._sequences(), sequences)

    def test_a_nfse_issued_by_the_company_keeps_the_withholdings_and_the_net(self):
        documents, errors, _warnings = self._import(
            nfse_xml(
                taker=UNKNOWN_PROVIDER, provider=LUCRO_PRESUMIDO, withholdings=True
            ),
        )
        self.assertFalse(errors)
        self.assertAlmostEqual(documents.amount_tax_withholding, 61.5)
        self.assertAlmostEqual(documents.amount_financial_total, 938.5)
        self.assertIn("938.50", str(documents.edi_payment_summary))

    def test_the_company_as_taker_and_provider_is_the_taker_and_the_note_enters(self):
        parsed = self.Document._edi_import_read(
            "a.xml", nfse_xml(taker=LUCRO_PRESUMIDO, provider=LUCRO_PRESUMIDO)
        )
        self.assertEqual(
            parsed.company_vats,
            (("taker", LUCRO_PRESUMIDO), ("issuer", LUCRO_PRESUMIDO)),
        )
        documents, errors, _warnings = self._import(
            nfse_xml(taker=LUCRO_PRESUMIDO, provider=LUCRO_PRESUMIDO)
        )
        self.assertFalse(errors)
        self.assertEqual(documents.fiscal_operation_type, "in")
        self.assertEqual(documents.issuer, "partner")

    def test_the_description_of_the_taxation_code_is_the_declared_nature(self):
        documents, _errors, _warnings = self._import(nfse_xml())
        self.assertEqual(
            documents.partner_operation_name, "Análise e desenvolvimento de sistemas."
        )

    def test_a_user_who_cannot_create_contacts_is_told_which_partner_is_missing(self):
        user = self._fiscal_user("fiscal_user_nfse_partner", self.presumed)
        model = self.Document.with_user(user).with_context(
            allowed_company_ids=self.presumed.ids
        )
        documents, errors, _warnings = self._import(
            nfse_xml(provider=UNKNOWN_PROVIDER), model
        )
        self.assertFalse(documents)
        self.assertIn("EMPRESA PRESTADORA DE TESTE LTDA", errors[0][1])
        self.assertIn("12.345.678/0001-95", errors[0][1])
        self.assertIn("not allowed to create contacts", errors[0][1])
        issued, errors, _warnings = self._import(
            nfse_xml(taker=OTHER_UNKNOWN, provider=LUCRO_PRESUMIDO), model
        )
        self.assertFalse(issued)
        self.assertIn("EMPRESA TOMADORA DE TESTE LTDA", errors[0][1])
        self.assertIn("11.444.777/0001-61", errors[0][1])

    def _registry(self, partners):
        """What is registered of each partner: the import never changes it."""
        names = (
            "name legal_name street_name street_number district zip city_id state_id "
            "l10n_br_ie_code l10n_br_im_code phone email"
        ).split()
        partners.invalidate_recordset()
        return {partner.id: [partner[name] for name in names] for partner in partners}

    def _registered(self, cnpj):
        return self.env["res.partner"].create(
            {
                "name": "Registered as is",
                "legal_name": "Registered legal name",
                "vat": formata(cnpj),
                "is_company": True,
                "country_id": self.env.ref("base.br").id,
                "state_id": self.env.ref("base.state_br_sp").id,
                "city_id": self.env.ref("l10n_br_base.city_3550308").id,
                "street_name": "Registered street",
                "street_number": "999",
                "district": "Registered district",
                "zip": "20000-000",
                "l10n_br_ie_code": "110042490114",
                "l10n_br_im_code": "222222",
                "phone": "21 99999-0000",
                "email": "registered@example.com",
            }
        )

    def _review_and_confirm(self, documents):
        line = documents.fiscal_line_ids
        line.product_id = self.env["product.product"].create(
            {"name": "Reviewed service", "type": "service"}
        )
        line.action_resolve_line()
        documents.action_document_confirm()

    def _assert_registry_untouched(self, content, issued):
        partner = self._registered(UNKNOWN_PROVIDER)
        company = self.presumed
        watched = partner | company.partner_id
        before = (company.name, self._registry(watched))
        documents, errors, _warnings = self._import(content)
        self.assertFalse(errors)
        self.assertEqual(documents.partner_id, partner)
        self._review_and_confirm(documents)
        self.assertEqual((company.name, self._registry(watched)), before)

    def test_a_registered_provider_and_the_company_are_never_written(self):
        self._assert_registry_untouched(nfse_xml(provider=UNKNOWN_PROVIDER), False)

    def test_a_registered_taker_and_the_company_are_never_written(self):
        content = nfse_xml(taker=UNKNOWN_PROVIDER, provider=LUCRO_PRESUMIDO)
        self._assert_registry_untouched(content, True)

    def test_a_provider_with_other_address_is_reported_and_left_as_it_is(self):
        provider = self._registered(UNKNOWN_PROVIDER)
        content = nfse_xml(provider=UNKNOWN_PROVIDER)
        documents, errors, _warnings = self._import(content)
        self.assertFalse(errors)
        self.assertEqual(documents.partner_id, provider)
        self.assertIn("Name", documents.import_partner_warning)
        self.assertIn(
            "EMPRESA PRESTADORA DE TESTE LTDA", documents.import_partner_warning
        )
        self.assertIn("Registered legal name", documents.import_partner_warning)
        self.assertEqual(provider.legal_name, "Registered legal name")

    def test_data_that_differ_only_in_case_and_punctuation_raise_no_warning(self):
        provider = self._registered(UNKNOWN_PROVIDER)
        provider.write({"legal_name": "empresa prestadora de teste ltda."})
        documents, _errors, _warnings = self._import(
            nfse_xml(provider=UNKNOWN_PROVIDER)
        )
        self.assertNotIn(
            "Registered as is - Name", documents.import_partner_warning or ""
        )

    def test_a_homonym_with_another_cnpj_is_not_matched(self):
        self._registered(OTHER_UNKNOWN).write(
            {
                "name": "EMPRESA PRESTADORA DE TESTE LTDA",
                "legal_name": "EMPRESA PRESTADORA DE TESTE LTDA",
            }
        )
        documents, errors, _warnings = self._import(nfse_xml(provider=UNKNOWN_PROVIDER))
        self.assertFalse(errors)
        self.assertEqual(documents.partner_id.cnpj_cpf_stripped, UNKNOWN_PROVIDER)

    def test_an_imported_nfse_without_issuing_gets_a_clear_message_for_the_pdf(self):
        documents, _errors, _warnings = self._import(nfse_xml())
        self.assertFalse(documents.file_report_id)
        with patch(
            "odoo.addons.l10n_br_nfse.models.document.filter_processador_edoc_nfse",
            lambda record: False,
        ), self.assertRaisesRegex(UserError, "printed version of an imported NFS-e"):
            NfseDocument.make_pdf(documents)

    def test_the_pdf_message_of_the_nfse_is_not_given_for_another_type(self):
        documents, _errors, _warnings = self._import(nfse_xml())
        documents.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
        mro = type(documents).__mro__
        following = next(
            cls for cls in mro[mro.index(NfseDocument) + 1 :] if "make_pdf" in vars(cls)
        )
        with patch(
            "odoo.addons.l10n_br_nfse.models.document.filter_processador_edoc_nfse",
            lambda record: False,
        ), patch.object(following, "make_pdf", return_value="next"):
            self.assertEqual(NfseDocument.make_pdf(documents), "next")

    def test_a_common_fiscal_user_opens_the_imported_nfse(self):
        if "nfe.40.di" in self.env:
            self.skipTest(
                "the form reads the NF-e models: their rules are of l10n_br_nfe"
            )
        user = self._fiscal_user("fiscal_user_nfse_form", self.presumed)
        model = self.Document.with_user(user).with_context(
            allowed_company_ids=self.presumed.ids
        )
        documents, errors, _warnings = self._import(nfse_xml(), model)
        self.assertFalse(errors)
        with Form(documents.with_user(user)) as form:
            form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_compras")

    def test_the_line_of_a_nfse_comes_with_the_operation_line_of_the_service(self):
        for content, xmlid in (
            (nfse_xml(), "l10n_br_fiscal.fo_compras_servico"),
            (
                nfse_xml(taker=UNKNOWN_PROVIDER, provider=LUCRO_PRESUMIDO),
                "l10n_br_fiscal.fo_venda_servico",
            ),
        ):
            documents, errors, _warnings = self._import(content)
            self.assertFalse(errors)
            self.assertEqual(
                documents.fiscal_line_ids.fiscal_operation_line_id,
                self.env.ref(xmlid),
            )
            self.assertNotIn("operation line", documents.import_warning or "")
            documents.unlink()

    def test_a_operation_without_a_service_line_leaves_the_line_pending(self):
        operation_line = self.env.ref("l10n_br_fiscal.fo_compras_servico")
        operation_line.state = "draft"
        documents, errors, _warnings = self._import(nfse_xml())
        self.assertFalse(errors)
        self.assertFalse(documents.fiscal_line_ids.fiscal_operation_line_id)
        self.assertIn("choose the operation line", documents.import_warning)

    def test_choosing_the_operation_line_of_the_nfse_keeps_its_taxes(self):
        if "nfe.40.di" in self.env:
            self.skipTest(
                "the form reads the NF-e models: their rules are of l10n_br_nfe"
            )
        user = self._fiscal_user("fiscal_user_nfse_line", self.presumed)
        documents, errors, _warnings = self._import(
            nfse_xml(
                taker=UNKNOWN_PROVIDER, provider=LUCRO_PRESUMIDO, withholdings=True
            )
        )
        self.assertFalse(errors)
        documents.document_serie_id = self.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "7",
                "name": "7",
                "document_type_id": documents.document_type_id.id,
                "company_id": self.presumed.id,
            }
        )
        line = documents.fiscal_line_ids
        before = (
            line.fiscal_tax_ids,
            line.issqn_value,
            line.pis_wh_value,
            line.fiscal_amount_total,
            documents.fiscal_amount_total,
        )
        self.assertTrue(before[0])
        operation_line = self.env.ref("l10n_br_fiscal.fo_venda_servico")
        line.fiscal_operation_line_id = False
        documents = documents.with_user(user).with_context(
            allowed_company_ids=self.presumed.ids
        )
        with Form(documents) as form:
            with form.fiscal_line_ids.edit(0) as line_form:
                line_form.fiscal_operation_line_id = operation_line
        line = documents.fiscal_line_ids
        self.assertEqual(line.fiscal_operation_line_id, operation_line)
        self.assertEqual(
            (
                line.fiscal_tax_ids,
                line.issqn_value,
                line.pis_wh_value,
                line.fiscal_amount_total,
                documents.fiscal_amount_total,
            ),
            before,
        )

    def test_the_demo_documents_show_the_import_and_the_confirmation(self):
        documents = self.Document.search(
            [
                (
                    "document_key",
                    "in",
                    [
                        "42024042259594315000157000000000000126031234567890",
                        "42024042281583054000129000000000090226031234567896",
                    ],
                )
            ],
            order="document_key",
        )
        if not documents:
            self.skipTest("the demo data is not installed")
        received, issued = documents
        service = self.env.ref("l10n_br_fiscal.customized_development_sale")
        self.assertEqual(received.issuer, "partner")
        self.assertEqual(received.state_edoc, "em_digitacao")
        self.assertGreater(received.amount_tax_withholding, 0.0)
        self.assertEqual(received.fiscal_line_ids.product_id, service)
        self.assertEqual(issued.issuer, "company")
        self.assertEqual(issued.state_edoc, "autorizada")
        self.assertEqual(issued.fiscal_line_ids.product_id, service)
        self.assertTrue(issued.fiscal_line_ids.fiscal_operation_line_id)

    def test_choosing_the_product_and_resolving_keeps_the_taxes_of_the_file(self):
        if "nfe.40.di" in self.env:
            self.skipTest(
                "the form reads the NF-e models: their rules are of l10n_br_nfe"
            )
        self.presumed.nfse_import_product_id = False
        user = self._fiscal_user("fiscal_user_nfse_product", self.presumed)
        documents, errors, _warnings = self._import(
            nfse_xml(
                taker=UNKNOWN_PROVIDER, provider=LUCRO_PRESUMIDO, withholdings=True
            )
        )
        self.assertFalse(errors)
        documents.document_serie_id = self.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "7",
                "name": "7",
                "document_type_id": documents.document_type_id.id,
                "company_id": self.presumed.id,
            }
        )
        line = documents.fiscal_line_ids
        before = (
            line.fiscal_tax_ids,
            line.issqn_value,
            line.pis_wh_value,
            line.fiscal_amount_total,
            line.tax_icms_or_issqn,
            line.service_type_id,
        )
        self.assertTrue(before[0])
        self.assertEqual(before[4], "issqn")
        product = self.env["product.product"].create(
            {"name": "Service", "type": "service"}
        )
        documents = documents.with_user(user).with_context(
            allowed_company_ids=self.presumed.ids
        )
        with Form(documents) as form:
            with form.fiscal_line_ids.edit(0) as line_form:
                line_form.product_id = product
        action = documents.fiscal_line_ids.action_resolve_line()
        self.assertEqual(action, {"type": "ir.actions.client", "tag": "reload"})
        self.env.flush_all()
        self.env.invalidate_all()
        line = documents.fiscal_line_ids
        self.assertEqual(line.product_id, product)
        self.assertEqual(
            (
                line.fiscal_tax_ids,
                line.issqn_value,
                line.pis_wh_value,
                line.fiscal_amount_total,
                line.tax_icms_or_issqn,
                line.service_type_id,
            ),
            before,
        )

    def test_the_service_of_an_nfse_issued_by_the_company_is_never_created(self):
        content = nfse_xml(taker=UNKNOWN_PROVIDER, provider=LUCRO_PRESUMIDO)
        products = self.env["product.product"].search_count([])
        documents, _errors, _warnings = self._import(content)
        line = documents.fiscal_line_ids
        self.assertFalse(line.product_id)
        self.assertEqual(line.import_state, "pending")
        self.presumed.nfse_import_product_id = self.env["product.product"].create(
            {"name": "Default service", "type": "service"}
        )
        products += 1
        documents.unlink()
        documents, _errors, _warnings = self._import(content)
        self.assertEqual(documents.fiscal_line_ids.import_state, "matched")
        self.assertEqual(self.env["product.product"].search_count([]), products)

    def test_the_company_is_the_taker_of_the_service(self):
        parsed = self.Document._edi_import_read("a.xml", nfse_xml(taker=LUCRO_REAL))
        self.assertEqual(
            parsed.company_vats, (("taker", LUCRO_REAL), ("issuer", PROVIDER))
        )
        self.assertEqual((parsed.reader, parsed.document_type_code), ("nfse", "SE"))
        self.assertEqual(parsed.issuer_vat, PROVIDER)
        documents, errors, _warnings = self._import(nfse_xml(taker=LUCRO_REAL))
        self.assertFalse(errors)
        self.assertEqual(documents.company_id, self.other_company)

    def test_a_nfse_for_no_company_is_refused(self):
        documents, errors, _warnings = self._import(
            nfse_xml(taker=UNKNOWN_PROVIDER, provider=OTHER_UNKNOWN)
        )
        self.assertFalse(documents)
        self.assertIn("No company of this database", errors[0][1])

    def test_a_nfse_without_a_valid_access_key_is_refused(self):
        content = nfse_xml().replace(b'Id="NFS4202404', b'Id="NFS420')
        documents, errors, _warnings = self._import(content)
        self.assertFalse(documents)
        self.assertIn("50-digit access key", errors[0][1])

    def test_a_file_that_is_not_a_nfse_is_left_to_the_next_reader(self):
        """Only this reader is called: what the others do with the file is theirs."""
        mro = type(self.Document).__mro__
        following = next(
            cls
            for cls in mro[mro.index(NfseReader) + 1 :]
            if "_edi_import_read" in vars(cls)
        )
        nfe = '<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe"><NFe/></nfeProc>'
        cte = '<cteProc xmlns="http://www.portalfiscal.inf.br/cte"><CTe/></cteProc>'
        with patch.object(following, "_edi_import_read", return_value="next"):
            for content in (nfe, cte, "<root/>", "not xml at all"):
                self.assertEqual(
                    NfseReader._edi_import_read(
                        self.Document, "a.xml", content.encode()
                    ),
                    "next",
                )
            read = NfseReader._edi_import_read(self.Document, "a.xml", nfse_xml())
        self.assertEqual(read.reader, "nfse")

    def test_the_same_nfse_twice_opens_the_same_document(self):
        documents, _errors, _warnings = self._import(nfse_xml())
        again, errors, warnings = self._import(nfse_xml())
        self.assertEqual(again, documents)
        self.assertFalse(errors)
        self.assertEqual(len(warnings), 1)

    def test_the_provider_that_is_unknown_is_created_and_recorded(self):
        self.assertFalse(
            self.env["res.partner"].search(
                [("cnpj_cpf_stripped", "=", UNKNOWN_PROVIDER)], limit=1
            )
        )
        documents, errors, _warnings = self._import(nfse_xml(provider=UNKNOWN_PROVIDER))
        self.assertFalse(errors)
        provider = documents.partner_id
        self.assertEqual(provider.cnpj_cpf_stripped, UNKNOWN_PROVIDER)
        self.assertEqual(provider.legal_name, "EMPRESA PRESTADORA DE TESTE LTDA")
        self.assertTrue(provider.is_company)
        self.assertIn(
            provider.display_name,
            " ".join(documents.message_ids.mapped("body")),
        )

    def test_the_service_product_of_the_company_goes_to_the_line(self):
        product = self.env["product.product"].create(
            {"name": "Imported NFS-e service", "type": "service"}
        )
        self.presumed.nfse_import_product_id = product
        documents, _errors, _warnings = self._import(nfse_xml())
        self.assertEqual(documents.fiscal_line_ids.product_id, product)

    def test_a_nfse_without_withholdings_has_no_page(self):
        documents, _errors, _warnings = self._import(nfse_xml())
        self.assertEqual(documents.amount_tax_withholding, 0.0)
        self.assertFalse(documents.edi_payment_summary)

    def test_a_nfse_with_withholdings_shows_them_and_the_net_amount(self):
        documents, errors, _warnings = self._import(nfse_xml(withholdings=True))
        self.assertFalse(errors)
        line = documents.fiscal_line_ids
        self.assertAlmostEqual(line.pis_wh_value, 6.5)
        self.assertAlmostEqual(line.cofins_wh_value, 30.0)
        self.assertAlmostEqual(line.irpj_wh_value, 15.0)
        self.assertAlmostEqual(line.csll_wh_value, 10.0)
        self.assertAlmostEqual(documents.amount_tax_withholding, 61.5)
        self.assertAlmostEqual(documents.amount_financial_total, 938.5)
        self.assertEqual(documents._edi_get_installments(), [])
        summary = str(documents.edi_payment_summary)
        for text in (
            "Withholdings",
            "1,000.00",
            "61.50",
            "Net amount payable",
            "938.50",
        ):
            self.assertIn(text, summary)

    def test_every_withholding_of_the_file_has_value_base_and_tax(self):
        documents, errors, _warnings = self._import(
            nfse_xml(withholdings=True).replace(b"<tpRetISSQN>1<", b"<tpRetISSQN>2<"),
        )
        self.assertFalse(errors)
        line = documents.fiscal_line_ids
        expected = {
            "issqn_wh": (20.0, 1000.0, "tax_issqn_wh_2"),
            "pis_wh": (6.5, 1000.0, "tax_pis_wh_0_65"),
            "cofins_wh": (30.0, 1000.0, "tax_cofins_wh_3"),
            "irpj_wh": (15.0, 1000.0, "tax_irpj_wh_1"),
            "csll_wh": (10.0, 1000.0, "tax_csll_wh_1"),
        }
        for prefix, (value, base, xmlid) in expected.items():
            self.assertAlmostEqual(line[f"{prefix}_value"], value, msg=prefix)
            self.assertAlmostEqual(line[f"{prefix}_base"], base, msg=prefix)
            self.assertEqual(
                line[f"{prefix}_tax_id"],
                self.env.ref(f"l10n_br_fiscal.{xmlid}"),
                prefix,
            )
            self.assertIn(line[f"{prefix}_tax_id"], line.fiscal_tax_ids, prefix)
        withheld = sum(value for value, _base, _xmlid in expected.values())
        self.assertAlmostEqual(documents.amount_tax_withholding, withheld)
        self.assertAlmostEqual(
            documents.amount_financial_total, line.amount_fiscal - withheld
        )

    def test_confirming_a_nfse_issued_by_the_company_neither_sends_nor_learns(self):
        content = nfse_xml(taker=UNKNOWN_PROVIDER, provider=LUCRO_PRESUMIDO)
        documents, _errors, _warnings = self._import(content)
        self.assertEqual(documents.fiscal_operation_type, "out")
        line = documents.fiscal_line_ids
        line.product_id = self.env["product.product"].create(
            {"name": "Service", "type": "service"}
        )
        line.action_resolve_line()
        sequences = self._sequences()
        documents.action_document_confirm()
        self.assertEqual(documents.state_edoc, "autorizada")
        self.assertEqual(documents.document_number, "1")
        self.assertEqual(self._sequences(), sequences)
        self.assertFalse(documents.send_file_id)
        self.assertFalse(
            self.env["product.supplierinfo"].search(
                [("partner_id", "=", documents.partner_id.id)]
            )
        )

    def test_a_common_fiscal_user_imports_a_nfse(self):
        user = self._fiscal_user("fiscal_user_nfse", self.presumed)
        model = self.Document.with_user(user).with_context(
            allowed_company_ids=self.presumed.ids
        )
        documents, errors, _warnings = self._import(nfse_xml(withholdings=True), model)
        self.assertFalse(errors)
        self.assertEqual(documents.create_uid, user)
        self.assertAlmostEqual(documents.amount_tax_withholding, 61.5)
        self.assertIn("61.50", str(documents.edi_payment_summary))
