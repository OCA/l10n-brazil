import base64
import logging
import os

from odoo.tests import SavepointCase

_logger = logging.getLogger(__name__)


class NFeImportWizardTest(SavepointCase):
    def setUp(self):
        super(NFeImportWizardTest, self).setUp()
        self.wizard = self.env["l10n_br_nfe.import_xml"].create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "importing_type": "xml_file",
            }
        )
        path = os.path.dirname(os.path.abspath(__file__))
        path_1 = path + (
            "/nfe/v4_00/leiauteNFe/NFe35200159594315000157550010000000012062777161.xml"
        )
        with open(path_1, "rb") as f:
            self.xml_1 = f.read()
        path_2 = path + (
            "/nfe/v4_00/leiauteNFe/NFe35200181583054000129550010000000052062777166.xml"
        )
        with open(path_2, "rb") as f:
            self.xml_2 = f.read()

    def test_onchange_nfe_xml(self):
        xml = self.xml_1
        wizard = self.wizard
        wizard.nfe_xml = base64.b64encode(xml)
        wizard._onchange_partner_id()
        # Check wizard header info
        self.assertEqual(
            wizard.document_key, "35200159594315000157550010000000012062777161"
        )
        self.assertEqual(wizard.document_number, "1")
        self.assertEqual(wizard.document_serie, "1")
        self.assertEqual(wizard.partner_cpf_cnpj, "59.594.315/0001-57")
        self.assertEqual(wizard.partner_name, "TESTE - Simples Nacional")
        self.assertEqual(
            wizard.partner_id, self.env.ref("l10n_br_base.simples_nacional_partner")
        )
        # Check wizard product info
        self.assertEqual(
            wizard.imported_products_ids[0].product_name, "[E-COM11] Cabinet with Doors"
        )
        self.assertEqual(wizard.imported_products_ids[0].uom_com, "UNID")
        self.assertEqual(wizard.imported_products_ids[0].quantity_com, 1)
        self.assertEqual(wizard.imported_products_ids[0].price_unit_com, 14)
        self.assertEqual(wizard.imported_products_ids[0].uom_trib, "UNID")
        self.assertEqual(wizard.imported_products_ids[0].quantity_trib, 1)
        self.assertEqual(wizard.imported_products_ids[0].price_unit_trib, 14)
        self.assertEqual(wizard.imported_products_ids[0].total, 14)

    def test_match_country_state_city(self):
        xml = self.xml_2
        wizard = self.wizard
        product_10 = self.env.ref("product.product_product_10")
        wizard.nfe_xml = base64.b64encode(xml)
        wizard._onchange_partner_id()
        wizard.imported_products_ids[0].product_id = product_10
        wizard.imported_products_ids[0].uom_internal = product_10.uom_id
        action = wizard.import_nfe_xml()
        edoc = self.env["l10n_br_fiscal.document"].browse(action["res_id"])
        delivery_adress = edoc.partner_id.child_ids[0]
        self.assertFalse(delivery_adress.country_id)
        self.assertFalse(delivery_adress.crc_state_id)
        self.assertFalse(delivery_adress.city_id)
