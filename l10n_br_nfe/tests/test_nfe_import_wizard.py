import base64
import io
import os
import re
import zipfile
from unittest.mock import MagicMock, patch

import nfelib
import pkg_resources
from xsdata.formats.dataclass.parsers import XmlParser

from odoo.exceptions import UserError
from odoo.tests import TransactionCase

from odoo.addons import l10n_br_nfe

from ..wizards.document_import_wizard import DocumentImportWizard


class NFeImportWizardTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        def test_xml_path(filename):
            return os.path.join(
                l10n_br_nfe.__path__[0],
                "tests",
                "nfe",
                "v4_00",
                "leiauteNFe",
                filename,
            )

        path_1 = test_xml_path("NFe35200181583054000129550010000000052062777166.xml")
        with open(path_1, "rb") as f:
            cls.xml_1 = f.read()

        cls.wizard = False
        cls.product_1 = cls.env["product.product"].create({"name": "Product Test 1"})
        cls.partner_1 = cls.env["res.partner"].create({"name": "Partner Test 1"})

    def _prepare_wizard(self, xml):
        self.wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "file": base64.b64encode(xml),
            }
        )
        self.wizard._onchange_file()

    def check_edoc(self, edoc):
        self.assertEqual(
            len(self.wizard.imported_products_ids),
            len(edoc.fiscal_line_ids),
        )
        self.assertTrue(edoc.partner_id)
        self.assertEqual(
            self.wizard.issuer_partner_id.vat,
            edoc.partner_id.vat,
        )
        self.assertEqual(
            self.wizard.issuer_partner_id.name,
            edoc.partner_id.name,
        )

    def test_import_nfe_xml(self):
        xml = "dummy"
        with self.assertRaises(ValueError):
            self._prepare_wizard(xml.encode("utf-8"))

        mock_document = MagicMock(spec=["modelo_documento"])
        mock_document.modelo_documento = "65"
        with (
            patch.object(
                DocumentImportWizard,
                "_extract_binding_data",
                return_value=mock_document,
            ),
            self.assertRaises(TypeError),
        ):
            self.wizard._check_xml_data(self.wizard._parse_file())

        self._prepare_wizard(self.xml_1)
        self.wizard._import_edoc()

        self.check_edoc(self.wizard.document_id)

        first_imported_product = self.wizard.imported_products_ids[0]

        self.assertEqual(
            self.wizard.document_key,
            "3520 0181 5830 5400 0129 5500 1000 0000 0520 6277 7166",
        )
        self.assertEqual(self.wizard.document_number, "5")
        self.assertEqual(self.wizard.document_serie, "1")
        self.assertEqual(self.wizard.issuer_partner_id.vat, "81.583.054/0001-29")
        self.assertEqual(self.wizard.issuer_partner_id.name, "Empresa Lucro Presumido")
        self.assertEqual(
            self.wizard.partner_id,
            self.env.ref("l10n_br_base.lucro_presumido_partner"),
        )
        self.assertEqual(
            f"[{first_imported_product.product_code}] "
            f"{first_imported_product.product_name}",
            "[E-COM11] Cabinet with Doors",
        )
        self.assertEqual(first_imported_product.uom_com, "UNID")
        self.assertEqual(first_imported_product.quantity_com, 1)
        self.assertEqual(first_imported_product.price_unit_com, 14)
        self.assertEqual(first_imported_product.uom_trib, "UNID")
        self.assertEqual(first_imported_product.quantity_trib, 1)
        self.assertEqual(first_imported_product.price_unit_trib, 14)
        self.assertEqual(first_imported_product.total, 14)

    def test_create_edoc_from_xml(self):
        self._prepare_wizard(self.xml_1)

        self.wizard.partner_id = False
        binding, edoc = self.wizard._create_edoc_from_file()
        self.assertEqual(self.wizard.partner_id, edoc.partner_id)

        self.check_edoc(edoc)

    def FIXME_test_set_fiscal_operation_type(self):
        self._prepare_wizard(self.xml_1)

        doc = self.wizard._document_key_from_binding(self.wizard._parse_file())
        origin_company = self.wizard.company_id

        doc_company_id = self.env["res.company"].search(
            [("cnpj_cpf_stripped", "=", re.sub("[^0-9]", "", doc.cnpj_cpf_emitente))],
            limit=1,
        )
        self.wizard.company_id = doc_company_id
        self.wizard._set_fiscal_operation_type()
        self.assertEqual(self.wizard.fiscal_operation_type, "out")

        self.wizard.company_id = origin_company
        self.wizard._set_fiscal_operation_type()
        self.assertEqual(self.wizard.fiscal_operation_type, "in")

    def test_import_creates_reviewed_draft(self):
        """The import materializes a faithful document with per-line review
        states, the original XML attached and the supplier nomenclature
        preserved; the supplier info learning happens on the persisted
        line."""
        self._prepare_wizard(self.xml_1)
        self.wizard._import_edoc()
        document = self.wizard.document_id

        self.assertTrue(document.imported_document)
        self.assertTrue(document.import_state)
        self.assertTrue(all(line.import_state for line in document.fiscal_line_ids))
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "l10n_br_fiscal.document"),
                ("res_id", "=", document.id),
                ("name", "=ilike", "%.xml"),
            ]
        )
        self.assertTrue(attachment)

        line = document.fiscal_line_ids[0]
        # supplier nomenclature preserved on the line (spec fields)
        self.assertTrue(line.nfe40_cProd)
        self.assertEqual(line._get_partner_product_code(), line.nfe40_cProd)
        # the commercial unit declared in the file is persisted as the
        # snapshot: nfe40_uCom is a related of the INTERNAL unit and would
        # follow the de-para
        declared_uom_code = self.wizard._parse_file().infNFe.det[0].prod.uCom
        self.assertEqual(line.partner_uom_code, declared_uom_code)

        # supplier info learning on the persisted line
        line._apply_import_depara()
        self.assertEqual(line.import_state, "resolved")
        self.assertEqual(line.partner_uom_code, declared_uom_code)
        self.assertTrue(line.import_supplierinfo_id)
        self.assertEqual(line.import_supplierinfo_id.product_code, line.nfe40_cProd)

    def test_import_binding_without_product_creation(self):
        """With create_missing_products=False an unmatched product line is
        left empty (pending review) instead of created as a side effect."""
        xml = self.xml_1.decode()
        xml = xml.replace("E-COM11", "NAOEXISTE1").replace(
            "Cabinet with Doors", "Produto Desconhecido XYZ"
        )
        binding = XmlParser().from_bytes(xml.encode())
        products_before = self.env["product.product"].search_count([])
        document = self.env["l10n_br_fiscal.document"].import_binding_nfe(
            binding, edoc_type="in", create_missing_products=False
        )
        self.assertEqual(self.env["product.product"].search_count([]), products_before)
        self.assertFalse(document.fiscal_line_ids[0].product_id)
        document._init_import_states()
        self.assertEqual(document.fiscal_line_ids[0].import_state, "pending")
        self.assertEqual(document.import_state, "pending")

    def _nfelib_sample_xml(self):
        res_items = (
            "nfe",
            "samples",
            "v4_0",
            "leiauteNFe",
            "35180834128745000152550010000474281920007498-nfe.xml",
        )
        return pkg_resources.resource_stream(
            nfelib.__name__, "/".join(res_items)
        ).read()

    def _zip_wizard(self, entries):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for name, content in entries:
                archive.writestr(name, content)
        return self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "file": base64.b64encode(buffer.getvalue()),
            }
        )

    def test_zip_batch_import(self):
        """A zip archive with several XMLs lands as several persisted
        documents waiting for review."""
        other_xml = self._nfelib_sample_xml()

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("nota1.xml", self.xml_1)
            archive.writestr("nota2.xml", other_xml)
            archive.writestr("leiame.txt", b"nao sou um xml")

        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "file": base64.b64encode(buffer.getvalue()),
            }
        )
        self.assertTrue(wizard._file_is_zip())
        documents = wizard._import_edoc_batch()
        self.assertEqual(len(documents), 2)
        self.assertTrue(all(documents.mapped("imported_document")))

    def test_zip_batch_isolates_a_failing_entry(self):
        """An entry that fails after touching the database must not poison
        the transaction: the files after it are still imported and the
        failure is reported as a warning."""
        wizard = self._zip_wizard(
            [
                ("01-nota.xml", self.xml_1),
                ("02-quebrada.xml", self.xml_1),
                ("03-nota.xml", self._nfelib_sample_xml()),
            ]
        )
        wizard_model = type(wizard)
        original_import = wizard_model._import_edoc
        calls = []

        def flaky_import(entry):
            calls.append(entry)
            if len(calls) == 2:
                # a real database error, which aborts the transaction:
                # without a savepoint per entry every later file would fail
                # with "current transaction is aborted"
                entry.env.cr.execute("SELECT id FROM tabela_que_nao_existe")
            return original_import(entry)

        logger = "odoo.addons.l10n_br_fiscal.wizards.document_import_wizard"
        with patch.object(wizard_model, "_import_edoc", flaky_import):
            with self.assertLogs(logger, level="WARNING") as log:
                documents = wizard._import_edoc_batch()

        self.assertEqual(len(calls), 3)
        self.assertEqual(len(documents), 2)
        self.assertTrue(any("02-quebrada.xml" in message for message in log.output))

    def test_zip_batch_with_no_importable_entry_raises(self):
        """When every entry fails there is nothing to review: the user gets
        the errors instead of an empty list of documents."""
        wizard = self._zip_wizard([("01-quebrada.xml", b"<NFe>nao sou uma NFe</NFe>")])
        with self.assertRaises(UserError):
            wizard._import_edoc_batch()

    def test_match_xml_product(self):
        self._prepare_wizard(self.xml_1)

        xml = self.wizard._parse_file()
        xml_product_1 = xml.infNFe.det[0].prod
        prod_id = self.wizard._match_product(xml_product_1)
        self.assertEqual(prod_id, self.env.ref("product.product_product_10"))

        prod_code = self.env["product.product"].create(
            {
                "name": "TEST1",
                "default_code": "TEST123",
            }
        )

        mock_code = MagicMock(spec=["cProd"])
        mock_code.cProd = "TEST123"
        prod_id = self.wizard._match_product(mock_code)

        mock_code = MagicMock(spec=["cProd"])
        mock_code.cProd = "TEST123"
        prod_id = self.wizard._match_product(mock_code)
        self.assertEqual(prod_id, prod_code)

        prod_code.unlink()
        prod_barcode = self.env["product.product"].create(
            {"name": "TEST2", "barcode": "123456789123"}
        )
        mock_barcode = MagicMock(spec=["cEANTrib"])
        mock_barcode.cProd = False
        mock_barcode.cEANTrib = "123456789123"
        prod_id = self.wizard._match_product(mock_barcode)
        self.assertEqual(prod_id, prod_barcode)

        prod_barcode.unlink()
        prod_id = self.wizard._match_product(MagicMock())
        self.assertFalse(prod_id)

    def test_match_product_by_purchase(self):
        """The purchase-order priority match is a soft dependency on
        l10n_br_purchase (which adds partner_order/partner_order_line to
        purchase.order.line). It must be a no-op when those fields are absent,
        so _match_product falls back to supplierinfo/default_code/barcode."""
        self._prepare_wizard(self.xml_1)
        pol = self.env.get("purchase.order.line")
        has_fields = pol is not None and "partner_order" in pol._fields
        mock = MagicMock()
        mock.xPed = "NONEXISTENT-PO-REF"
        mock.nItemPed = "999"
        # No PO references this xPed (and/or l10n_br_purchase absent) -> no
        # match, and crucially no crash on a missing field.
        self.assertFalse(self.wizard._match_product_by_purchase(mock))
        if not has_fields:
            # guard short-circuits before any purchase.order.line search
            self.assertFalse(
                self.wizard._match_product_by_purchase(
                    self.wizard._parse_file().infNFe.det[0].prod
                )
            )

    def test__parse_xml(self):
        self._prepare_wizard(self.xml_1)

        first_product = self.wizard.imported_products_ids[0]
        first_product.new_cfop_id = self.env.ref("l10n_br_fiscal.cfop_5111").id

        # The parsed binding is NEVER rewritten anymore: the file keeps the
        # supplier data (audit trail) and the CFOP override is applied on
        # the persisted document line instead.
        xml = self.wizard._parse_file()
        first_xml_product = xml.infNFe.det[0].prod
        self.assertEqual(first_xml_product.CFOP, "5102")

        self.wizard._import_edoc()
        self.assertEqual(
            self.wizard.document_id.fiscal_line_ids[0].cfop_id.code, "5111"
        )

        mock_prod = MagicMock(spec=["imposto"])
        mock_prod.imposto.ICMS.ICMS60.pICMS = 60
        mock_prod.imposto.ICMS.ICMS60.vICMS = 100
        mock_prod.imposto.IPI.IPITrib.pIPI = 5
        mock_prod.imposto.IPI.IPITrib.vIPI = 100
        taxes = self.wizard._get_taxes_from_xml_product(mock_prod)

        self.assertEqual(taxes["pICMS"], 60)
        self.assertEqual(taxes["vICMS"], 100)
        self.assertEqual(taxes["pIPI"], 5)
        self.assertEqual(taxes["vIPI"], 100)

    def test_cfop_warning(self):
        """The wizard line flags a CFOP whose scope (intra/interstate) is
        inconsistent with the real issuer/company geography."""
        sp = self.env.ref("base.state_br_sp")
        rj = self.env.ref("base.state_br_rj")
        company = self.env.ref("base.main_company")
        company.state_id = sp
        issuer = self.env["res.partner"].create(
            {"name": "Issuer SP", "state_id": sp.id}
        )
        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {"company_id": company.id, "issuer_partner_id": issuer.id}
        )
        line = self.env["l10n_br_fiscal.document.import.wizard.line"].create(
            {"import_xml_id": wizard.id}
        )

        # interstate CFOP but both parties in SP -> warn
        line.cfop_xml = "6101"
        self.assertTrue(line.cfop_warning)

        # intrastate CFOP and both parties in SP -> no warning
        line.cfop_xml = "1101"
        self.assertFalse(line.cfop_warning)

        # issuer now in RJ: intrastate CFOP is inconsistent -> warn
        issuer.state_id = rj
        line._compute_cfop_warning()
        self.assertTrue(line.cfop_warning)

        # interstate CFOP with issuer RJ / company SP -> consistent, no warning
        line.cfop_xml = "6101"
        line._compute_cfop_warning()
        self.assertFalse(line.cfop_warning)
