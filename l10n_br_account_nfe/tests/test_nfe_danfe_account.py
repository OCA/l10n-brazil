# Copyright 2024 Engenere.one
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import os
from unittest.mock import patch

from odoo.tests import SavepointCase, tagged

from odoo.addons.l10n_br_nfe import __path__ as nfe_path


@tagged("post_install", "-at_install")
class TestDanfe(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        def test_xml_path(filename):
            return os.path.join(
                nfe_path[0],
                "tests",
                "nfe",
                "v4_00",
                "leiauteNFe",
                filename,
            )

        path = test_xml_path("NFe35200181583054000129550010000000052062771230.xml")
        with open(path, "rb") as f:
            cls.xml = f.read()

        cls.wizard = False
        cls.partner_1 = cls.env["res.partner"].create({"name": "Partner Test 1"})

    def _prepare_wizard(self, xml):
        self.wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "file": base64.b64encode(xml),
            }
        )
        self.wizard._onchange_file()

    def test_generate_danfe_brazil_fiscal_report(self):
        nfe = self.env.ref("l10n_br_account_nfe.demo_nfe_dados_de_cobranca")
        nfe.action_post()

        danfe_report = self.env["ir.actions.report"].search(
            [("report_name", "=", "main_template_danfe_account")]
        )
        danfe_pdf = danfe_report._render_qweb_pdf([nfe.id])
        self.assertTrue(danfe_pdf)

    def test_generate_danfe_erpbrasil_edoc(self):
        nfe = self.env.ref("l10n_br_account_nfe.demo_nfe_dados_de_cobranca")
        nfe.company_id.danfe_library = "erpbrasil.edoc.pdf"

        with patch("erpbrasil.edoc.pdf.base.ImprimirXml.imprimir") as mock_make_pdf:
            mock_make_pdf.return_value = b"Mock PDF"

            nfe.action_post()

            danfe_report = self.env["ir.actions.report"].search(
                [("report_name", "=", "main_template_danfe_account")]
            )
            danfe_pdf = danfe_report._render_qweb_pdf([nfe.id])
            self.assertTrue(danfe_pdf)

    def test_import_nfe_invoice(self):
        # Create a product.supplier.info
        tmpl1_id = self.env.ref("product.product_product_10_product_template")
        prod1_id = tmpl1_id.product_variant_id
        prod1_id.seller_ids = self.env["product.supplierinfo"].create(
            {
                "name": self.partner_1.id,
                "product_code": "E-COM11",
                "product_name": "Cabinet with Doors",
                "product_id": prod1_id.id,
                "partner_uom": "U",
                "partner_uom_factor": 1,
            }
        )

        self._prepare_wizard(self.xml)
        binding, edoc = self.wizard._import_edoc()

        # Ensure product was recognized
        self.assertEqual(edoc.fiscal_line_ids.product_id, prod1_id)

        # Confirm import and generate the invoice
        edoc.action_import_confirm()
        move_ids = edoc.fiscal_line_ids.account_line_ids.mapped("move_id")

        # Ensure move_ids were created
        self.assertNotEqual(move_ids, False)

        move_id = move_ids[0]
        for line in move_id.financial_move_line_ids[:-1]:
            self.assertEqual(line.credit, 46)
        self.assertEqual(move_id.financial_move_line_ids[-1].credit, 48)
