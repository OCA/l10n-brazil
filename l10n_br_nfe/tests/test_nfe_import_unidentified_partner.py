# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import importlib.resources
import re

import nfelib
from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc

from odoo.tests import TransactionCase

SAMPLE = (
    "nfe",
    "samples",
    "v4_0",
    "leiauteNFe",
    "35180834128745000152550010000474281920007498-nfe.xml",
)


class TestNFeImportUnidentifiedPartner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.xml = (
            importlib.resources.files(nfelib.__name__)
            .joinpath(*SAMPLE)
            .read_bytes()
            .decode()
        )

    def _import(self, xml):
        return self.env["l10n_br_fiscal.document"].import_binding_nfe(
            TnfeProc.from_xml(xml), edoc_type="in", dry_run=False
        )

    def test_import_transporta_without_name_and_cnpj(self):
        xml = re.sub(
            r"<transporta>.*?</transporta>",
            "<transporta><UF>SP</UF></transporta>",
            self.xml,
            flags=re.S,
        )
        nfe = self._import(xml)
        self.assertTrue(nfe.id)
        self.assertFalse(nfe.nfe40_transporta)

    def test_import_entrega_without_cnpj_has_no_parent(self):
        # A partner without vat used to be picked as parent by vat = False
        self.env["res.partner"].create({"name": "Partner without vat"})
        entrega = (
            "<entrega><CNPJ/><xLgr>Rua da Entrega</xLgr><nro>324</nro>"
            "<xBairro>Centro</xBairro><cMun>3550308</cMun><xMun>SAO PAULO</xMun>"
            "<UF>SP</UF><CEP>01001000</CEP></entrega>"
        )
        nfe = self._import(self.xml.replace("</dest>", "</dest>" + entrega, 1))
        shipping = nfe.partner_shipping_id
        self.assertTrue(shipping)
        self.assertEqual(shipping.type, "delivery")
        self.assertFalse(shipping.parent_id)
        self.assertEqual(shipping.nfe40_xLgr, "Rua da Entrega")

    def _import_entrega(self, entrega):
        nfe = self._import(self.xml.replace("</dest>", "</dest>" + entrega, 1))
        return nfe.partner_shipping_id

    def test_import_entrega_without_cpais_brazilian_uf(self):
        # cPais is optional in the layout; a Brazilian UF implies Brazil
        shipping = self._import_entrega(
            "<entrega><CNPJ/><xLgr>Rua da Entrega</xLgr><nro>324</nro>"
            "<xBairro>Centro</xBairro><cMun>3550308</cMun><xMun>SAO PAULO</xMun>"
            "<UF>SP</UF><CEP>01001000</CEP></entrega>"
        )
        self.assertEqual(shipping.street_name, "Rua da Entrega")
        self.assertEqual(shipping.street_number, "324")
        self.assertEqual(shipping.district, "Centro")
        self.assertEqual(shipping.city_id, self.env.ref("l10n_br_base.city_3550308"))
        self.assertEqual(shipping.state_id, self.env.ref("base.state_br_sp"))
        self.assertEqual(shipping.country_id, self.env.ref("base.br"))

    def test_import_entrega_without_cpais_foreign_uf(self):
        # With UF=EX and no cPais the country is unknown: address is not set
        shipping = self._import_entrega(
            "<entrega><CNPJ/><xLgr>Foreign Street</xLgr><nro>10</nro>"
            "<xBairro>Downtown</xBairro><cMun>9999999</cMun><xMun>EXTERIOR</xMun>"
            "<UF>EX</UF></entrega>"
        )
        # country_id is not checked: l10n_br_base defaults it to Brazil when
        # the company is Brazilian, regardless of the imported address
        self.assertFalse(shipping.street_name)
        self.assertFalse(shipping.street_number)
        self.assertFalse(shipping.district)
        self.assertFalse(shipping.state_id)

    def test_import_entrega_with_cpais(self):
        shipping = self._import_entrega(
            "<entrega><CNPJ/><xLgr>Rua da Entrega</xLgr><nro>324</nro>"
            "<xBairro>Centro</xBairro><cMun>3550308</cMun><xMun>SAO PAULO</xMun>"
            "<UF>SP</UF><CEP>01001000</CEP><cPais>1058</cPais><xPais>BRASIL</xPais>"
            "</entrega>"
        )
        self.assertEqual(shipping.street_name, "Rua da Entrega")
        self.assertEqual(shipping.state_id, self.env.ref("base.state_br_sp"))
        self.assertEqual(shipping.country_id, self.env.ref("base.br"))
