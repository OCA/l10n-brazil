# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import importlib

import nfelib
from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc

from odoo.exceptions import UserError
from odoo.tests import TransactionCase

SAMPLE = (
    "nfe",
    "samples",
    "v4_0",
    "leiauteNFe",
    "35180834128745000152550010000474281920007498-nfe.xml",
)

DECLARATION = (
    "<DI>"
    "<nDI>0000001</nDI><dDI>2026-08-01</dDI>"
    "<xLocDesemb>Santos</xLocDesemb><UFDesemb>SP</UFDesemb>"
    "<dDesemb>2026-08-05</dDesemb><tpViaTransp>1</tpViaTransp>"
    "<tpIntermedio>2</tpIntermedio><CNPJ>11222333000181</CNPJ>"
    "<UFTerceiro>SP</UFTerceiro><cExportador>EXP001</cExportador>"
    "<adi><nAdicao>1</nAdicao><nSeqAdic>1</nSeqAdic>"
    "<cFabricante>FAB001</cFabricante></adi>"
    "<adi><nAdicao>2</nAdicao><nSeqAdic>2</nSeqAdic>"
    "<cFabricante>FAB002</cFabricante></adi>"
    "</DI>"
)

IMPORT_TAX = (
    "<II><vBC>1000.00</vBC><vDespAdu>0.00</vDespAdu>"
    "<vII>140.00</vII><vIOF>0.00</vIOF></II>"
)


class TestNFeImportDeclaration(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquirer = cls.env["res.partner"].create(
            {
                "name": "Adquirente da importação",
                "is_company": True,
                "vat": "11222333000181",
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_sp").id,
            }
        )

    def _sample_xml(self):
        resource_path = "/".join(SAMPLE)
        stream = importlib.resources.files(nfelib.__name__).joinpath(resource_path)
        with stream.open("rb") as handle:
            return handle.read().decode()

    def test_the_declaration_keeps_the_customs_state_and_the_acquirer(self):
        declaration = self.env["nfe.40.di"].create(
            {
                "nfe40_nDI": "0000001",
                "nfe40_dDI": "2026-08-01",
                "nfe40_xLocDesemb": "Santos",
                "nfe40_UFDesemb": "SP",
                "nfe40_dDesemb": "2026-08-05",
                "nfe40_tpViaTransp": "1",
                "nfe40_tpIntermedio": "2",
                "nfe40_cExportador": "EXP001",
                "nfe40_CNPJ": "11222333000181",
            }
        )
        self.assertEqual(
            declaration.state_clearance_id, self.env.ref("base.state_br_sp")
        )
        self.assertEqual(declaration.nfe40_UFDesemb, "SP")
        self.assertEqual(declaration.partner_acquirer_id, self.acquirer)
        self.assertEqual(declaration.nfe40_CNPJ, "11222333000181")

    def test_the_imported_nfe_brings_the_declaration_and_the_import_tax(self):
        xml = self._sample_xml()
        xml = xml.replace("</indTot>", "</indTot>" + DECLARATION, 1)
        xml = xml.replace("<PIS>", IMPORT_TAX + "<PIS>", 1)

        document = self.env["l10n_br_fiscal.document"].import_binding_nfe(
            TnfeProc.from_xml(xml), edoc_type="in", dry_run=False
        )
        line = document.fiscal_line_ids[0]

        self.assertEqual(len(line.nfe40_DI), 1)
        declaration = line.nfe40_DI
        self.assertEqual(declaration.nfe40_nDI, "0000001")
        self.assertEqual(declaration.nfe40_xLocDesemb, "Santos")
        self.assertEqual(
            declaration.state_clearance_id, self.env.ref("base.state_br_sp")
        )
        self.assertEqual(declaration.partner_acquirer_id, self.acquirer)
        self.assertEqual(
            declaration.partner_acquirer_id.state_id, self.env.ref("base.state_br_sp")
        )
        self.assertEqual(len(declaration.nfe40_adi), 2)
        self.assertEqual(
            declaration.nfe40_adi.mapped("nfe40_cFabricante"), ["FAB001", "FAB002"]
        )

        self.assertEqual(line.ii_base, 1000.0)
        self.assertEqual(line.ii_value, 140.0)
        self.assertEqual(line.ii_percent, 14.0)
        self.assertEqual(line.ii_tax_id.percent_amount, 14.0)

    def _import_document(self, cfop_ref):
        company = self.env.ref("l10n_br_base.empresa_lucro_presumido")
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": company.id,
                "partner_id": self.env.ref("l10n_br_base.res_partner_exterior").id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "document_serie": "1",
                "document_number": "910001",
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_compras").id,
                "fiscal_operation_type": "in",
            }
        )
        self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": document.id,
                "name": "Mercadoria importada",
                "product_id": self.env.ref("product.product_product_7").id,
                "quantity": 1,
                "price_unit": 1000.0,
                "fiscal_operation_type": "in",
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_compras").id,
                "fiscal_operation_line_id": self.env.ref(
                    "l10n_br_fiscal.fo_compras_compras"
                ).id,
                "cfop_id": self.env.ref(cfop_ref).id,
            }
        )
        return document

    def test_a_line_with_an_import_cfop_needs_the_declaration(self):
        document = self._import_document("l10n_br_fiscal.cfop_3101")
        with self.assertRaises(UserError) as error:
            document._document_check()
        self.assertIn("525", str(error.exception))

        document.fiscal_line_ids[0].nfe40_DI = [
            (
                0,
                0,
                {
                    "nfe40_nDI": "0000002",
                    "nfe40_dDI": "2026-08-01",
                    "nfe40_xLocDesemb": "Santos",
                    "nfe40_UFDesemb": "SP",
                    "nfe40_dDesemb": "2026-08-05",
                    "nfe40_tpViaTransp": "1",
                    "nfe40_tpIntermedio": "1",
                    "nfe40_cExportador": "EXP002",
                },
            )
        ]
        self.assertTrue(document._document_check())

    def test_the_returned_import_cfops_do_not_need_the_declaration(self):
        document = self._import_document("l10n_br_fiscal.cfop_3201")
        self.assertTrue(document._document_check())
