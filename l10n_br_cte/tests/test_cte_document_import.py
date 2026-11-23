# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from datetime import date
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tools import file_open

from odoo.addons.l10n_br_cte.models.document import CTe as CteDocument
from odoo.addons.l10n_br_cte.models.document_import import Document as CteReader
from odoo.addons.l10n_br_cte.models.res_city import ResCity
from odoo.addons.l10n_br_cte.models.res_company import ResCompany
from odoo.addons.l10n_br_cte.models.res_country import ResCountry
from odoo.addons.l10n_br_cte.models.res_country_state import ResCountryState
from odoo.addons.l10n_br_cte.models.res_partner import ResPartner
from odoo.addons.l10n_br_fiscal_edi.tests.common import EdiImportCase
from odoo.addons.l10n_br_fiscal_edi.tools import EdiInstallment

CTE_KEY = "35240759594315000157570010000057311040445890"
CTE_FILE = f"l10n_br_cte/tests/cte/v4_00/leiauteCTe/CTe{CTE_KEY}.xml"
# CNPJ of the recipient in the file, and of the companies of the demo data
FILE_RECIPIENT = "46081676000158"
LUCRO_REAL = "46312887000154"
LUCRO_PRESUMIDO = "81583054000129"
COLLECTION = (
    "<cobr><fat><nFat>1</nFat><vOrig>100.00</vOrig><vLiq>100.00</vLiq></fat>"
    "<dup><nDup>002</nDup><dVenc>2027-01-10</dVenc><vDup>60.00</vDup></dup>"
    "<dup><nDup>001</nDup><dVenc>2026-12-10</dVenc><vDup>40.00</vDup></dup>"
    "</cobr>"
)
NAMESPACE = "http://www.portalfiscal.inf.br/cte"
PROTOCOL = (
    '<protCTe versao="4.00"><infProt><tpAmb>2</tpAmb><verAplic>SP_CTE_PL_4.00'
    "</verAplic><chCTe>%(key)s</chCTe><dhRecbto>2024-07-10T10:00:00-03:00"
    "</dhRecbto><nProt>135240000000002</nProt><digVal>YWJj</digVal>"
    "<cStat>%(status)s</cStat><xMotivo>x</xMotivo></infProt></protCTe>"
)


OTHER_DOCUMENT = (
    "<infOutros><tpDoc>99</tpDoc><descOutros>Contract</descOutros><nDoc>7</nDoc>"
    "<dEmi>2024-07-01</dEmi><vDocFisc>50.00</vDocFisc></infOutros>"
)


def cte_xml(
    collection=None,
    taker=None,
    recipient=LUCRO_REAL,
    status=None,
    related=False,
    emitter=None,
    shipper=None,
):
    """The demo CT-e, with the recipient moved to a company of the demo data.

    :param collection: the ``cobr`` group to add to the CT-e
    :param taker: CNPJ of a taker that is not the recipient (``toma4``)
    :param emitter: CNPJ of the issuer, when it is not the one of the file
    :param shipper: CNPJ of the shipper (``exped``), when it is not the one of the file
    :param status: cStat of the protocol; the CT-e then comes as a ``cteProc``
    """
    with file_open(CTE_FILE, "rb") as handle:
        xml = handle.read().decode()
    xml = xml.replace(FILE_RECIPIENT, recipient)
    if emitter:
        xml = re.sub(r"(<emit>\s*<CNPJ>)\d+", rf"\g<1>{emitter}", xml)
    if related:
        xml = xml.replace("</infNFe>", f"</infNFe>{OTHER_DOCUMENT}", 1)
    if collection:
        xml = xml.replace("</infCTeNorm>", f"{collection}</infCTeNorm>")
    if taker:
        xml = xml.replace(
            "<toma3>\n        <toma>3</toma>\n      </toma3>",
            f"<toma4><toma>4</toma><CNPJ>{taker}</CNPJ><xNome>Taker</xNome></toma4>",
        )
    if shipper:
        xml = re.sub(r"(<exped>\s*<CNPJ>)\d+", rf"\g<1>{shipper}", xml)
    if status:
        body = xml.split("?>", 1)[1].strip()
        xml = (
            f'<cteProc xmlns="{NAMESPACE}" versao="4.00">{body}'
            + PROTOCOL % {"key": CTE_KEY, "status": status}
            + "</cteProc>"
        )
    return xml.encode()


class TestCteDocumentImport(EdiImportCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.presumed = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        # the demo data sets the default products of this company
        cls.presumed.cte_import_product_id = False
        cls.presumed.cte_import_service_product_id = False
        # the demo CT-e of the Simples Nacional company has this key
        cls.Document.search([("document_key", "=", CTE_KEY)]).unlink()
        # and the demo CT-e of the company that issues the number of the file
        cls.Document.search(
            [
                ("company_id", "=", cls.presumed.id),
                ("document_type_id.code", "=", "57"),
                ("document_number", "=", "573"),
            ]
        ).unlink()

    def _import(self, content, model=None, operation=False, issued=False):
        """Import the file; with ``operation``, a person has chosen the operation of
        the document and of its line, as the review asks."""
        documents, errors, warnings = (
            self.Document if model is None else model
        )._edi_import_files([(f"{CTE_KEY}.xml", content)])
        if operation and documents:
            prefix = "fo_venda" if issued else "fo_compras"
            documents.fiscal_operation_id = self.env.ref(f"l10n_br_fiscal.{prefix}")
            documents.fiscal_line_ids.fiscal_operation_line_id = self.env.ref(
                f"l10n_br_fiscal.{prefix}_{'venda' if issued else 'compras'}"
            )
        return documents, errors, warnings

    def _freight(self, **values):
        return self.env["product.product"].create(
            dict({"name": "Freight service", "type": "service"}, **values)
        )

    def test_the_import_of_a_cte_creates_no_document_besides_its_own(self):
        """A group of the file is not a document: the list of the imported documents
        has no empty line, with or without documents referenced in the CT-e."""
        for content in (cte_xml(), cte_xml(related=True, collection=COLLECTION)):
            known = self.Document.with_context(active_test=False).search([])
            documents, errors, _warnings = self._import(content)
            self.assertFalse(errors)
            created = self.Document.with_context(active_test=False).search(
                [("id", "not in", known.ids)]
            )
            self.assertEqual(created, documents)
            documents.unlink()

    def test_no_imported_document_of_the_demo_is_empty(self):
        """Neither the demo of this module nor the one of the CT-e of the framework
        leave a document without type among the imported ones."""
        empty = self.Document.search(
            [("imported_document", "=", True), ("document_type_id", "=", False)]
        )
        self.assertFalse(empty)

    def test_the_demo_documents_show_the_import(self):
        received = self.Document.search(
            [("document_key", "=", "35240759594315000157570010000070011570007018")]
        )
        issued = self.Document.search(
            [("document_key", "=", "35240781583054000129570010000070021570007029")]
        )
        if not received:
            self.skipTest("the demo data is not installed")
        freight = self.env.ref("l10n_br_cte.product_freight_purchased")
        transport = self.env.ref("l10n_br_cte.product_transport_provided")
        self.assertEqual(received.issuer, "partner")
        self.assertEqual(received.fiscal_line_ids.product_id, freight)
        self.assertEqual(len(received.cte40_cobr.cte40_dup), 2)
        self.assertEqual(len(received._edi_get_installments()), 2)
        self.assertEqual(issued.issuer, "company")
        self.assertEqual(issued.state_edoc, "autorizada")
        self.assertEqual(issued.fiscal_line_ids.product_id, transport)

    def test_the_nature_of_the_operation_of_the_file_is_kept(self):
        documents, _errors, _warnings = self._import(cte_xml())
        self.assertEqual(documents.partner_operation_name, "Venda")
        content = cte_xml(recipient="12345678000195", emitter=LUCRO_PRESUMIDO)
        issued, _errors, _warnings = self._import(content)
        self.assertEqual(issued.partner_operation_name, "Venda")

    def test_the_default_freight_product_is_a_suggestion_on_the_line(self):
        dozen = self.env.ref("uom.product_uom_dozen")
        # a received CT-e is a purchase: the line takes the purchase unit
        product = self._freight(uom_id=dozen.id, uom_po_id=dozen.id)
        self.other_company.cte_import_product_id = product
        documents, errors, _warnings = self._import(cte_xml())
        self.assertFalse(errors)
        line = documents.fiscal_line_ids
        self.assertEqual(line.product_id, product)
        self.assertEqual(line.uom_id, dozen)
        self.assertEqual(line.import_state, "matched")

    def test_without_the_default_product_the_line_waits_for_the_choice(self):
        documents, _errors, _warnings = self._import(cte_xml())
        line = documents.fiscal_line_ids
        self.assertFalse(line.product_id)
        self.assertEqual(line.import_state, "pending")

    def test_confirming_the_suggestions_resolves_the_freight_line(self):
        self.other_company.cte_import_product_id = self._freight()
        documents, _errors, _warnings = self._import(cte_xml())
        self.assertEqual(documents.fiscal_line_ids.import_state, "matched")
        documents.action_import_confirm_suggestions()
        self.assertEqual(documents.fiscal_line_ids.import_state, "resolved")

    def test_a_product_of_another_company_is_not_suggested(self):
        self.other_company.cte_import_product_id = self._freight(
            company_id=self.presumed.id
        )
        user = self._fiscal_user("fiscal_user_cte_product", self.other_company)
        model = self.Document.with_user(user).with_context(
            allowed_company_ids=self.other_company.ids
        )
        documents, errors, _warnings = self._import(cte_xml(), model)
        self.assertFalse(errors)
        line = documents.fiscal_line_ids
        self.assertFalse(line.product_id)
        self.assertEqual(line.import_state, "pending")

    def test_a_cte_issued_by_the_company_does_not_get_the_freight_product(self):
        self.presumed.cte_import_product_id = self._freight()
        content = cte_xml(recipient="12345678000195", emitter=LUCRO_PRESUMIDO)
        documents, errors, _warnings = self._import(content)
        self.assertFalse(errors)
        self.assertFalse(documents.fiscal_line_ids.product_id)

    def test_the_transport_service_is_suggested_for_a_cte_of_the_company(self):
        content = cte_xml(recipient="12345678000195", emitter=LUCRO_PRESUMIDO)
        documents, _errors, _warnings = self._import(content)
        self.assertFalse(documents.fiscal_line_ids.product_id)
        self.assertEqual(documents.fiscal_line_ids.import_state, "pending")
        service = self._freight(name="Transport provided")
        self.presumed.cte_import_service_product_id = service
        self.Document.search([("document_key", "=", CTE_KEY)]).unlink()
        documents, errors, _warnings = self._import(content)
        self.assertFalse(errors)
        line = documents.fiscal_line_ids
        self.assertEqual((line.product_id, line.import_state), (service, "matched"))
        documents.action_import_confirm_suggestions()
        self.assertEqual(line.import_state, "resolved")

    def test_the_freight_bought_does_not_use_the_service_provided(self):
        self.other_company.cte_import_service_product_id = self._freight()
        documents, _errors, _warnings = self._import(cte_xml())
        self.assertFalse(documents.fiscal_line_ids.product_id)

    def test_a_user_who_cannot_create_contacts_is_told_which_partner_is_missing(self):
        user = self._fiscal_user("fiscal_user_cte_partner", self.other_company)
        model = self.Document.with_user(user).with_context(
            allowed_company_ids=self.other_company.ids
        )
        documents, errors, _warnings = self._import(
            cte_xml(emitter="12345678000195"), model
        )
        self.assertFalse(documents)
        message = errors[0][1]
        self.assertIn("Empresa Simples Nacional", message)
        self.assertIn("12.345.678/0001-95", message)
        self.assertIn("not allowed to create contacts", message)

    def test_the_partner_missing_for_a_cte_issued_by_the_company_is_its_taker(self):
        user = self._fiscal_user("fiscal_user_cte_taker", self.presumed)
        model = self.Document.with_user(user).with_context(
            allowed_company_ids=self.presumed.ids
        )
        content = cte_xml(recipient="12345678000195", emitter=LUCRO_PRESUMIDO)
        documents, errors, _warnings = self._import(content, model)
        self.assertFalse(documents)
        self.assertIn("12.345.678/0001-95", errors[0][1])
        self.assertNotIn("81.583.054/0001-29", errors[0][1])

    def _registered(self, cnpj):
        return self.env["res.partner"].create(
            {
                "name": "Registered as is",
                "legal_name": "Registered legal name",
                "vat": f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}",
                "is_company": True,
                "country_id": self.env.ref("base.br").id,
                "state_id": self.env.ref("base.state_br_sp").id,
                "city_id": self.env.ref("l10n_br_base.city_3550308").id,
                "street_name": "Registered street",
                "street_number": "999",
                "district": "Registered district",
                "zip": "01310-100",
                "l10n_br_ie_code": "110042490114",
                "l10n_br_im_code": "222222",
                "phone": "11 99999-0000",
                "email": "registered@example.com",
            }
        )

    def _assert_registry_untouched(self, content, company, issued):
        names = (
            "name legal_name street_name street_number district zip city_id state_id "
            "l10n_br_ie_code l10n_br_im_code phone email"
        ).split()
        partner = self._registered("12345678000195")
        watched = partner | company.partner_id

        def registry():
            watched.invalidate_recordset()
            return (company.name, [[p[name] for name in names] for p in watched])

        before = registry()
        documents, errors, _warnings = self._import(content)
        self.assertFalse(errors)
        self.assertEqual(documents.partner_id, partner)
        line = documents.fiscal_line_ids
        line.product_id = self._freight()
        line.action_resolve_line()
        documents.action_document_confirm()
        self.assertEqual(registry(), before)

    def test_a_registered_emitter_and_the_company_are_never_written(self):
        self._assert_registry_untouched(
            cte_xml(emitter="12345678000195"), self.other_company, False
        )

    def test_a_registered_taker_and_the_company_are_never_written(self):
        content = cte_xml(
            recipient="12345678000195", emitter=LUCRO_PRESUMIDO, status="100"
        )
        self._assert_registry_untouched(content, self.presumed, True)

    def test_a_homonym_with_another_cnpj_is_not_matched(self):
        self._registered("11444777000161").write(
            {
                "name": "Empresa Simples Nacional",
                "legal_name": "Empresa Simples Nacional",
            }
        )
        documents, errors, _warnings = self._import(cte_xml(emitter="12345678000195"))
        self.assertFalse(errors)
        self.assertEqual(documents.partner_id.cnpj_cpf_stripped, "12345678000195")

    def test_a_partner_with_other_address_and_state_tax_number_is_reported(self):
        partner = self._registered("12345678000195")
        documents, errors, _warnings = self._import(cte_xml(emitter="12345678000195"))
        self.assertFalse(errors)
        self.assertEqual(documents.partner_id, partner)
        warning = documents.import_partner_warning
        self.assertIn("Street", warning)
        self.assertIn("Registered street", warning)
        self.assertIn("State tax number", warning)
        self.assertEqual(partner.street_name, "Registered street")

    def test_data_that_differ_only_in_case_accent_and_punctuation_raise_no_warning(
        self
    ):
        content = cte_xml(emitter="12345678000195")
        partner = self._registered("12345678000195")
        parsed = self.Document._edi_import_read("a.xml", content)
        documents, _errors, _warnings = self._import(content)
        declared = {p: d for p, d in documents._edi_import_partner_data(parsed)}[
            partner
        ]
        city = self.env["res.city"].search([("name", "=ilike", declared.city)], limit=1)
        state = self.env["res.country.state"].search(
            [("code", "=", declared.state_code), ("country_id.code", "=", "BR")],
            limit=1,
        )
        partner.write(
            {
                "legal_name": declared.name.upper(),
                "street_name": declared.street.lower(),
                "street_number": declared.street_number,
                "district": declared.district,
                "zip": declared.zip_code,
                "l10n_br_ie_code": declared.state_tax_number,
                "city_id": city.id,
                "state_id": state.id,
            }
        )
        documents.import_partner_warning = False
        documents._edi_import_check_partners(parsed)
        self.assertNotIn("Registered as is", documents.import_partner_warning or "")

    def test_a_common_fiscal_user_sees_and_chooses_the_operation_of_the_imported_cte(
        self,
    ):
        user = self._fiscal_user("fiscal_user_cte_form", self.other_company)
        model = self.Document.with_user(user).with_context(
            allowed_company_ids=self.other_company.ids
        )
        documents, errors, _warnings = self._import(cte_xml(COLLECTION), model)
        self.assertFalse(errors)
        operation = self.env.ref("l10n_br_fiscal.fo_compras")
        with Form(documents.with_user(user)) as form:
            form.fiscal_operation_id = operation
        self.assertEqual(documents.fiscal_operation_id, operation)
        with Form(documents.fiscal_line_ids.with_user(user)) as line_form:
            self.assertEqual(line_form.name, "Frete")

    def test_the_page_of_a_cte_of_100_with_two_installments_shows_100_and_100(self):
        documents, _errors, _warnings = self._import(
            cte_xml(COLLECTION), operation=True
        )
        self.assertAlmostEqual(documents.fiscal_amount_total, 100.0)
        self.assertAlmostEqual(documents.amount_financial_total, 100.0)
        summary = str(documents.edi_payment_summary)
        self.assertEqual(summary.count("100.00"), 2)
        self.assertNotIn("add up", summary)

    def test_a_cte_is_read_and_becomes_a_document_of_the_recipient(self):
        documents, errors, _warnings = self._import(cte_xml(status="100"))
        self.assertFalse(errors)
        self.assertEqual(documents.document_key, CTE_KEY)
        self.assertEqual(documents.document_type_id.code, "57")
        self.assertEqual(documents.company_id, self.other_company)
        self.assertTrue(documents.imported_document)
        self.assertEqual(documents.issuer, "partner")
        self.assertEqual(documents.partner_id.cnpj_cpf_stripped, "59594315000157")
        self.assertTrue(documents.original_xml_file_id)
        line = documents.fiscal_line_ids
        self.assertEqual(line.partner_cfop_id.code, "5352")
        self.assertEqual(line.import_state, "pending")

    def test_the_status_comes_from_the_protocol_of_the_cte(self):
        for status, expected in (
            ("100", "authorized"),
            ("101", "cancelled"),
            ("110", "denied"),
            ("999", "unknown"),
        ):
            parsed = self.Document._edi_import_read("a.xml", cte_xml(status=status))
            self.assertEqual((parsed.status, parsed.status_code), (expected, status))
        parsed = self.Document._edi_import_read("a.xml", cte_xml())
        self.assertEqual((parsed.status, parsed.status_code), ("unknown", ""))

    def test_a_cte_whose_protocol_does_not_authorize_it_is_refused(self):
        documents, errors, _warnings = self._import(cte_xml(status="999"))
        self.assertFalse(documents)
        self.assertIn("not authorized (status 999)", errors[0][1])

    def test_a_cancelled_cte_is_refused(self):
        documents, errors, _warnings = self._import(cte_xml(status="101"))
        self.assertFalse(documents)
        self.assertIn("cancelled", errors[0][1])

    def test_the_company_is_the_taker_before_the_recipient(self):
        parsed = self.Document._edi_import_read("a.xml", cte_xml(taker=LUCRO_PRESUMIDO))
        self.assertEqual(
            parsed.company_vats,
            (
                ("taker", LUCRO_PRESUMIDO),
                ("recipient", LUCRO_REAL),
                ("recipient", "12046835000161"),
                ("recipient", "12046835000161"),
                ("recipient", "84148732000113"),
                ("issuer", "59594315000157"),
            ),
        )
        documents, errors, _warnings = self._import(cte_xml(taker=LUCRO_PRESUMIDO))
        self.assertFalse(errors)
        self.assertEqual(documents.company_id, self.presumed)

    def test_the_company_taker_of_the_cte_gets_the_invoice(self):
        """The taker owes the freight: nothing stops the invoice."""
        documents, errors, _warnings = self._import(cte_xml(taker=LUCRO_PRESUMIDO))
        self.assertFalse(errors)
        self.assertEqual(documents.cte_company_role, "taker")
        self.assertFalse(documents._edi_no_payable_reason())
        self.assertNotIn("not the taker", documents.import_warning or "")
        if "edi_can_generate_invoice" in documents._fields:
            self.assertNotIn("not the taker", documents.import_warning or "")

    def test_a_cte_of_which_the_company_is_only_the_recipient_is_only_registered(self):
        """The company is the recipient, not the taker: the CT-e is imported for
        the record, with a warning, and gives no invoice."""
        documents, errors, _warnings = self._import(cte_xml(taker="12345678000195"))
        self.assertFalse(errors)
        self.assertEqual(documents.company_id, self.other_company)
        self.assertEqual(documents.cte_company_role, "other")
        self.assertIn("not the taker", documents._edi_no_payable_reason())
        self.assertIn("not the taker", documents.import_warning)
        if hasattr(documents, "action_generate_invoice"):
            with self.assertRaises(UserError):
                documents.action_generate_invoice()
            self.assertFalse(documents.edi_can_generate_invoice)

    def test_the_shipper_and_the_receiver_are_not_the_taker_either(self):
        """The shipper, like the sender and the recipient, can be the company, and
        it is not the taker of the freight."""
        content = cte_xml(
            taker="12345678000195", shipper=LUCRO_REAL, recipient="9" * 14
        )
        parsed = self.Document._edi_import_read("a.xml", content)
        self.assertIn(("recipient", LUCRO_REAL), parsed.company_vats)
        documents, errors, _warnings = self._import(content)
        self.assertFalse(errors)
        self.assertEqual(documents.cte_company_role, "other")

    def test_the_company_is_the_recipient_when_the_taker_is_not_one(self):
        documents, errors, _warnings = self._import(cte_xml(taker="12345678000195"))
        self.assertFalse(errors)
        self.assertEqual(documents.company_id, self.other_company)

    def _sequences(self):
        return self.env["ir.sequence"].search([]).read(["id", "number_next_actual"])

    def test_a_cte_issued_by_the_company_becomes_an_outgoing_document(self):
        sequences = self._sequences()
        content = cte_xml(
            COLLECTION, recipient="12345678000195", emitter=LUCRO_PRESUMIDO
        )
        documents, errors, _warnings = self._import(content)
        self.assertFalse(errors)
        self.assertEqual(documents.fiscal_operation_type, "out")
        self.assertEqual(documents.company_id, self.presumed)
        self.assertEqual(documents.issuer, "company")
        self.assertEqual(documents.state_edoc, "em_digitacao")
        self.assertTrue(documents.imported_document)
        self.assertEqual(documents.partner_id.cnpj_cpf_stripped, "12345678000195")
        self.assertEqual(documents.document_key, CTE_KEY)
        self.assertEqual(
            (documents.document_number, documents.document_serie), ("573", "1")
        )
        self.assertAlmostEqual(documents.fiscal_line_ids.price_unit, 100.0)
        self.assertEqual(
            [i.amount for i in documents._edi_get_installments()], [40.0, 60.0]
        )
        self.assertEqual(self._sequences(), sequences)

    def test_confirming_a_cte_issued_by_the_company_neither_sends_nor_learns(self):
        self.presumed.cte_import_product_id = False
        # the protocol of the authorization comes with the file: a note the company
        # issued is confirmed as authorized only with it
        content = cte_xml(
            recipient="12345678000195", emitter=LUCRO_PRESUMIDO, status="100"
        )
        documents, _errors, _warnings = self._import(
            content, operation=True, issued=True
        )
        line = documents.fiscal_line_ids
        line.product_id = self._freight()
        line.action_resolve_line()
        sequences = self._sequences()
        documents.action_document_confirm()
        self.assertEqual(documents.state_edoc, "autorizada")
        self.assertEqual(documents.document_number, "573")
        self.assertEqual(self._sequences(), sequences)
        self.assertFalse(documents.send_file_id)
        self.assertFalse(
            self.env["product.supplierinfo"].search(
                [("partner_id", "=", documents.partner_id.id)]
            )
        )

    def _confirmed(self, content):
        documents, errors, _warnings = self._import(content, operation=True)
        self.assertFalse(errors)
        documents.fiscal_line_ids.write({"product_id": self._freight().id})
        documents.fiscal_line_ids.action_resolve_line()
        documents.action_document_confirm()
        return documents

    def test_the_dacte_of_an_imported_cte_is_printed_from_the_original_xml(self):
        for content in (
            cte_xml(recipient="12345678000195", emitter=LUCRO_PRESUMIDO, status="100"),
            cte_xml(status="100"),
        ):
            self.Document.search([("document_key", "=", CTE_KEY)]).write(
                {"state_edoc": "em_digitacao"}
            )
            self.Document.search([("document_key", "=", CTE_KEY)]).unlink()
            documents = self._confirmed(content)
            original = documents.original_xml_file_id.raw
            self.assertFalse(documents.file_report_id)
            self.assertFalse(documents.authorization_file_id)
            with patch(
                "odoo.addons.mail.models.mail_template.MailTemplate.send_mail"
            ) as send_mail:
                action = documents.view_pdf()
            self.assertFalse(send_mail.called)
            self.assertEqual(action["type"], "ir.actions.act_url")
            self.assertTrue(documents.file_report_id.raw.startswith(b"%PDF"))
            self.assertEqual(documents.original_xml_file_id.raw, original)
            self.assertFalse(documents.authorization_file_id)

    def test_confirming_an_imported_cte_prints_and_sends_nothing(self):
        mails = self.env["mail.mail"].search_count([])
        documents = self._confirmed(
            cte_xml(recipient="12345678000195", emitter=LUCRO_PRESUMIDO, status="100")
        )
        self.assertFalse(documents.file_report_id)
        self.assertEqual(self.env["mail.mail"].search_count([]), mails)

    def test_a_cte_where_the_company_is_issuer_and_taker_enters_as_the_taker(self):
        content = cte_xml(taker=LUCRO_PRESUMIDO, emitter=LUCRO_PRESUMIDO)
        documents, errors, _warnings = self._import(content)
        self.assertFalse(errors)
        self.assertEqual(documents.company_id, self.presumed)
        self.assertEqual(documents.issuer, "partner")
        self.assertEqual(documents.fiscal_operation_type, "in")

    def test_a_cte_for_no_company_is_refused(self):
        content = cte_xml(recipient="12345678000195", emitter="11444777000161")
        documents, errors, _warnings = self._import(content)
        self.assertFalse(documents)
        self.assertIn("No company of this database", errors[0][1])

    def test_a_cte_os_and_a_gtve_are_refused_with_the_reason(self):
        for root, kind in (
            ("cteOSProc", "CT-e OS"),
            ("CTeOS", "CT-e OS"),
            ("GTVe", "GTV-e"),
            ("GTVeProc", "GTV-e"),
            ("CTeSimp", "CT-e Simp"),
        ):
            content = f'<{root} xmlns="{NAMESPACE}" versao="4.00"/>'.encode()
            documents, errors, _warnings = self._import(content)
            self.assertFalse(documents, root)
            self.assertIn("Only the CT-e (model 57)", errors[0][1], root)
            self.assertIn(kind, errors[0][1], root)

    def test_a_broken_cte_is_refused_as_invalid(self):
        for content in (
            f'<cteProc xmlns="{NAMESPACE}"><CTe/></cteProc>',
            f'<CTe xmlns="{NAMESPACE}"><infCte Id="CTe123"/></CTe>',
            f'<cteProc xmlns="{NAMESPACE}"><unknown/></cteProc>',
        ):
            documents, errors, _warnings = self._import(content.encode())
            self.assertFalse(documents)
            self.assertIn("not a valid CT-e", errors[0][1])

    def test_a_file_that_is_not_a_cte_is_left_to_the_next_reader(self):
        """Only this reader is called: what the others do with the file is theirs."""
        mro = type(self.Document).__mro__
        following = next(
            cls
            for cls in mro[mro.index(CteReader) + 1 :]
            if "_edi_import_read" in vars(cls)
        )
        nfse = (
            '<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse"><infNFSe Id="NFS1"/>'
            "</NFSe>"
        )
        nfe = '<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe"><NFe/></nfeProc>'
        other_namespace = '<cteProc xmlns="http://example.com/other"/>'
        with patch.object(following, "_edi_import_read", return_value="next"):
            for content in (nfse, nfe, other_namespace, "not xml at all"):
                self.assertEqual(
                    CteReader._edi_import_read(
                        self.Document, "a.xml", content.encode()
                    ),
                    "next",
                )
            read = CteReader._edi_import_read(self.Document, "a.xml", cte_xml())
        self.assertEqual(read.reader, "cte")

    def test_the_overrides_of_the_cte_act_only_on_the_cte_schema(self):
        """The import dictionaries of another schema (NF-e, MDF-e) go to the next
        override of the chain, never to the rules of the CT-e."""
        cases = (
            (ResCity, "res.city", "match_or_create_m2o", ({"ibge_code": "1"}, {})),
            (ResCountry, "res.country", "match_or_create_m2o", ({"bc_code": "1"}, {})),
            (
                ResCountryState,
                "res.country.state",
                "match_or_create_m2o",
                ({"code": "SP"}, {}),
            ),
            (ResCompany, "res.company", "_prepare_import_dict", ({"x": 1},)),
            (ResPartner, "res.partner", "_prepare_import_dict", ({"x": 1},)),
            (ResPartner, "res.partner", "match_or_create_m2o", ({"cnpj_cpf": "1"}, {})),
            (
                CteDocument,
                "l10n_br_fiscal.document",
                "_prepare_import_dict",
                ({"x": 1},),
            ),
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
        self.assertGreaterEqual(checked, 3)

    def test_the_invoice_group_of_the_collection_changes_neither_number_nor_totals(
        self
    ):
        fat = self.env["cte.40.tcte_fat"]
        for name in ("cte40_nFat", "cte40_vOrig", "cte40_vDesc", "cte40_vLiq"):
            self.assertFalse(fat._fields[name].related, name)
        collection = COLLECTION.replace(
            "<nFat>1</nFat><vOrig>100.00</vOrig><vLiq>100.00</vLiq>",
            "<nFat>987654</nFat><vOrig>999.00</vOrig><vDesc>9.00</vDesc>"
            "<vLiq>990.00</vLiq>",
        )
        documents, errors, _warnings = self._import(cte_xml(collection))
        self.assertFalse(errors)
        self.assertEqual(documents.document_number, "573")
        self.assertAlmostEqual(documents.fiscal_line_ids.price_unit, 100.0)
        self.assertEqual(documents.cte40_cobr.cte40_fat.cte40_nFat, "987654")
        self.assertEqual(len(documents.cte40_cobr.cte40_dup), 2)

    def _operation_with_lines(self, count):
        """An operation of entry with ``count`` approved lines, none of which answers
        the CFOP of the CT-e."""
        operation = self.env["l10n_br_fiscal.operation"].create(
            {
                "code": f"CTE-{count}",
                "name": f"Operation with {count} line(s)",
                "fiscal_operation_type": "in",
                "fiscal_type": "purchase",
            }
        )
        for number in range(count):
            self.env["l10n_br_fiscal.operation.line"].create(
                {
                    "fiscal_operation_id": operation.id,
                    "name": f"Line {number}",
                    "cfop_internal_id": self.env.ref("l10n_br_fiscal.cfop_1102").id,
                    "product_type": "00",
                }
            )
        operation.action_approve()
        return operation

    def test_the_operation_chosen_in_the_header_waits_for_the_operation_line(self):
        """The CFOP of the CT-e matches no line of the operation and the operation has
        several candidates: the line is left to the person, with a warning; once the
        person chooses the operation line, the amounts are the ones of the file."""
        # no line of the demo answers the CFOP of the CT-e here (the purchase
        # operation has the freight ones, which the next test takes)
        operation_line = type(self.env["l10n_br_fiscal.operation.line"])
        with patch.object(
            operation_line,
            "_find_by_issuer_cfop",
            lambda *args, **kwargs: self.env["l10n_br_fiscal.operation.line"],
        ):
            documents, errors, _warnings = self._import(cte_xml(COLLECTION))
        self.assertFalse(errors)
        operation = self._operation_with_lines(2)
        documents.fiscal_operation_id = operation
        line = documents.fiscal_line_ids
        self.assertFalse(line.fiscal_operation_line_id)
        self.assertIn("choose the operation line", documents.import_warning)
        line.fiscal_operation_line_id = operation.line_ids[:1]
        self.assertAlmostEqual(documents.fiscal_amount_total, 100.0)
        self.assertAlmostEqual(documents.amount_financial_total, 100.0)
        self.assertNotIn("add up", str(documents.edi_payment_summary))

    def test_the_freight_purchase_line_answers_the_cfop_of_the_cte(self):
        """The purchase operation has lines for the freight (CFOP 5352 and 5353 of
        the carrier): choosing it on the header gives the line its operation line
        by itself."""
        documents, errors, _warnings = self._import(cte_xml(COLLECTION))
        self.assertFalse(errors)
        documents.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_compras")
        line = documents.fiscal_line_ids
        self.assertTrue(line.fiscal_operation_line_id)
        self.assertNotIn("choose the operation line", documents.import_warning or "")
        self.assertAlmostEqual(documents.amount_financial_total, 100.0)

    def test_a_cte_with_a_collection_declares_its_installments_in_order(self):
        documents, errors, _warnings = self._import(cte_xml(COLLECTION))
        self.assertFalse(errors)
        self.assertEqual(len(documents.cte40_cobr.cte40_dup), 2)
        self.assertEqual(
            documents._edi_get_installments(),
            [
                EdiInstallment("001", date(2026, 12, 10), 40.0),
                EdiInstallment("002", date(2027, 1, 10), 60.0),
            ],
        )

    def test_the_page_of_a_cte_with_a_collection_shows_the_installments(self):
        documents, _errors, _warnings = self._import(
            cte_xml(COLLECTION), operation=True
        )
        summary = str(documents.edi_payment_summary)
        for text in ("001", "002", "40.00", "60.00", "12/10/2026", "01/10/2027"):
            self.assertIn(text, summary)
        self.assertFalse(documents._edi_installment_difference())
        self.assertNotIn("add up", summary)

    def test_installments_that_do_not_add_up_to_the_document_raise_a_warning(self):
        collection = COLLECTION.replace("60.00", "90.00")
        documents, _errors, _warnings = self._import(
            cte_xml(collection), operation=True
        )
        self.assertEqual(documents._edi_installment_difference(), -30.0)
        self.assertIn("add up", str(documents.edi_payment_summary))
        self.assertIn("add up", documents.import_warning)

    def test_the_installments_of_a_cte_are_never_taken_from_another_one(self):
        first, errors, _warnings = self._import(cte_xml(COLLECTION))
        self.assertFalse(errors)
        other = COLLECTION.replace("60.00", "90.00")
        second, errors, _warnings = self._import(
            cte_xml(other, emitter=LUCRO_PRESUMIDO, recipient="12345678000195")
        )
        self.assertFalse(errors)
        self.assertNotEqual(first, second)
        self.assertEqual(
            sorted(first.cte40_cobr.cte40_dup.mapped("cte40_vDup")), [40.0, 60.0]
        )
        self.assertEqual(
            sorted(second.cte40_cobr.cte40_dup.mapped("cte40_vDup")), [40.0, 90.0]
        )

    def test_a_cte_without_a_collection_declares_no_installment(self):
        documents, errors, _warnings = self._import(cte_xml())
        self.assertFalse(errors)
        self.assertEqual(documents._edi_get_installments(), [])
        self.assertFalse(documents.edi_payment_summary)

    def test_an_installment_without_date_or_amount_is_not_declared(self):
        collection = (
            "<cobr><dup><nDup>001</nDup><vDup>50.00</vDup></dup>"
            "<dup><nDup>002</nDup><dVenc>2026-12-10</dVenc></dup>"
            "<dup><nDup>003</nDup><dVenc>2026-12-20</dVenc><vDup>20.00</vDup></dup>"
            "</cobr>"
        )
        documents, _errors, _warnings = self._import(cte_xml(collection))
        self.assertEqual(
            documents._edi_get_installments(),
            [EdiInstallment("003", date(2026, 12, 20), 20.0)],
        )

    def test_another_type_of_document_declares_no_cte_installment(self):
        documents, _errors, _warnings = self._import(cte_xml(COLLECTION))
        documents.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
        self.assertEqual(documents._edi_get_installments(), [])

    def test_a_common_fiscal_user_imports_a_cte_with_every_related_document(self):
        user = self._fiscal_user("fiscal_user_cte_related", self.other_company)
        model = self.Document.with_user(user).with_context(
            allowed_company_ids=self.other_company.ids
        )
        documents, errors, _warnings = self._import(
            cte_xml(related=True), model, operation=True
        )
        self.assertFalse(errors)
        self.assertEqual(len(documents), 1)

    def test_a_common_fiscal_user_imports_a_cte(self):
        user = self._fiscal_user("fiscal_user_cte", self.other_company)
        model = self.Document.with_user(user).with_context(
            allowed_company_ids=self.other_company.ids
        )
        documents, errors, _warnings = self._import(
            cte_xml(COLLECTION), model, operation=True
        )
        self.assertFalse(errors)
        self.assertEqual(documents.create_uid, user)
        self.assertEqual(len(documents._edi_get_installments()), 2)
        self.assertIn("40.00", str(documents.edi_payment_summary))
