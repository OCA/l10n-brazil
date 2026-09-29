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
