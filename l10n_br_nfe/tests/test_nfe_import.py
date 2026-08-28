# Copyright 2021 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import importlib
import re

import nfelib
import pkg_resources
from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc

from odoo.models import NewId
from odoo.tests import TransactionCase


class NFeImportTest(TransactionCase):
    def test_import_in_nfe_dry_run(self):
        res_items = (
            "nfe",
            "samples",
            "v4_0",
            "leiauteNFe",
            "35180834128745000152550010000474281920007498-nfe.xml",
        )

        resource_path = "/".join(res_items)
        nfe_stream = importlib.resources.files(nfelib.__name__).joinpath(resource_path)
        with nfe_stream.open("rb") as fp:
            binding = TnfeProc.from_xml(fp.read().decode())
        nfe = self.env["l10n_br_fiscal.document"].import_binding_nfe(
            binding, edoc_type="in", dry_run=True
        )
        assert isinstance(nfe.id, NewId)
        self._check_nfe(nfe)

    def test_import_in_nfe(self):
        res_items = (
            "nfe",
            "samples",
            "v4_0",
            "leiauteNFe",
            "35180834128745000152550010000474281920007498-nfe.xml",
        )
        resource_path = "/".join(res_items)
        nfe_stream = importlib.resources.files(nfelib.__name__).joinpath(resource_path)
        with nfe_stream.open("rb") as fp:
            binding = TnfeProc.from_xml(fp.read().decode())
        nfe = self.env["l10n_br_fiscal.document"].import_binding_nfe(
            binding, edoc_type="in", dry_run=False
        )

        assert isinstance(nfe.id, int)
        self._check_nfe(nfe)

    def test_items_without_gtin_do_not_all_match_the_same_product(self):
        res_items = (
            "nfe",
            "samples",
            "v4_0",
            "leiauteNFe",
            "35180834128745000152550010000474281920007498-nfe.xml",
        )
        resource_path = "/".join(res_items)
        nfe_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        xml = nfe_stream.read().decode()
        xml = re.sub(r"<cEAN>[^<]*</cEAN>", "<cEAN>SEM GTIN</cEAN>", xml)
        xml = re.sub(
            r"<cEANTrib>[^<]*</cEANTrib>", "<cEANTrib>SEM GTIN</cEANTrib>", xml
        )

        binding = TnfeProc.from_xml(xml)
        nfe = self.env["l10n_br_fiscal.document"].import_binding_nfe(
            binding, edoc_type="in", dry_run=False
        )

        codes = [line.nfe40_cProd for line in nfe.fiscal_line_ids]
        self.assertEqual(len(set(codes)), len(codes))
        self.assertEqual(
            [line.product_id.default_code for line in nfe.fiscal_line_ids], codes
        )
        products = nfe.fiscal_line_ids.mapped("product_id")
        self.assertEqual(len(products), len(nfe.fiscal_line_ids))

    def _check_nfe(self, nfe):
        self.assertEqual(type(nfe)._name, "l10n_br_fiscal.document")
        self.assertEqual(
            nfe.document_type_id, self.env.ref("l10n_br_fiscal.document_55")
        )
        self.assertEqual(nfe.document_number, "47428")

        # here we check that emit and enderEmit
        # are now the supplier data (partner_id)
        self.assertEqual(nfe.partner_id.name, "Alimentos Saudaveis")
        # (CNPJ is not formated yet in dry run)
        self.assertTrue(nfe.partner_id.vat in ("34.128.745/0001-52", "34128745000152"))
        # this tests the _extract_related_values method for related values:
        self.assertEqual(nfe.partner_id.legal_name, "Alimentos Ltda.")

        # enderDest
        nfe.partner_id._inverse_nfe40_CEP()
        self.assertEqual(nfe.partner_id.street_name, "Rua Fonseca")  # related xLgr
        self.assertEqual(nfe.partner_id.zip, "13877-123")
        self.assertEqual(nfe.partner_id.nfe40_CEP, "13877123")
        self.assertEqual(nfe.partner_id.city_id.name, "São João da Boa Vista")

        # now we check that company_id is unchanged
        self.assertEqual(nfe.company_id, self.env.ref("base.main_company"))

        # this tests that value is not overrident by stacked default vals
        self.assertEqual(nfe.nfe40_modFrete, "0")  # (default is 9)

        # lines data
        self.assertEqual(len(nfe.fiscal_line_ids), 6)
        self.assertEqual(nfe.fiscal_line_ids[0].quantity, 6)
        # NOTE / FIXME price unit is rounded to 7.16 if create and 7.155 if dry run
        self.assertTrue(abs(nfe.fiscal_line_ids[0].price_unit - 7.16) < 0.01)
        self.assertTrue(abs(nfe.fiscal_line_ids[0].fiscal_price - 7.16) < 0.01)

        # impostos
        self.assertEqual(nfe.fiscal_line_ids[0].icms_base_type, "0")
        self.assertEqual(nfe.fiscal_line_ids[0].icms_cst_id.code, "00")
        self.assertEqual(nfe.fiscal_line_ids[0].icms_base, 50.60)
        self.assertEqual(nfe.fiscal_line_ids[0].icms_value, 6.07)
        self.assertEqual(nfe.fiscal_line_ids[0].ipi_value, 0)

        # products
        self.assertEqual(nfe.fiscal_line_ids[0].nfe40_nItem, "1")
        self.assertEqual(nfe.fiscal_line_ids[0].product_id.name, "QUINOA 100G (2X50G)")
        self.assertEqual(nfe.fiscal_line_ids[0].product_id.barcode, "7897846902086")
        self.assertEqual(
            nfe.fiscal_line_ids[0].product_id.ncm_id.name[0:14], "Trigo mourisco"
        )
        self.assertEqual(nfe.fiscal_line_ids[0].product_id.ncm_id.code, "1008.50.90")

        self.assertEqual(
            nfe.fiscal_line_ids[1].product_id.name, "QUINOA VEGETAIS 100G (2X50G)"
        )
        self.assertEqual(
            nfe.fiscal_line_ids[2].product_id.name, "QUINOA PICANTE 100G (2X50G)"
        )

    def test_import_in_nfe_delivery_address(self):
        """A purchase NFe with an <entrega> block must import the delivery
        address into the stored partner_shipping_id (nfe40_entrega is a
        non-stored computed field, so it cannot hold the imported value)."""
        res_items = (
            "nfe",
            "samples",
            "v4_0",
            "leiauteNFe",
            "35180834128745000152550010000474281920007498-nfe.xml",
        )
        resource_path = "/".join(res_items)
        nfe_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        xml = nfe_stream.read().decode()
        entrega = (
            "<entrega>"
            "<CNPJ>34128745000152</CNPJ>"
            "<xLgr>Rua da Entrega</xLgr><nro>999</nro><xBairro>Centro</xBairro>"
            "<cMun>3550308</cMun><xMun>SAO PAULO</xMun><UF>SP</UF>"
            "<CEP>01001000</CEP><cPais>1058</cPais><xPais>Brasil</xPais>"
            "</entrega>"
        )
        xml = xml.replace("</dest>", "</dest>" + entrega, 1)
        binding = TnfeProc.from_xml(xml)
        nfe = self.env["l10n_br_fiscal.document"].import_binding_nfe(
            binding, edoc_type="in", dry_run=False
        )
        shipping = nfe.partner_shipping_id
        self.assertTrue(shipping, "delivery address was not imported")
        self.assertNotEqual(shipping, nfe.partner_id)
        self.assertEqual(shipping.type, "delivery")
        self.assertEqual(shipping.street_name, "Rua da Entrega")
        self.assertEqual(shipping.zip, "01001-000")

    def test_import_in_nfe_creates_reduced_tax(self):
        """A purchase NFe line declaring an ICMS base reduction (CST 20 with
        pRedBC) for which the company has no matching fiscal tax must create a
        tax carrying that percent_reduction, instead of falling back to a
        plain no-reduction tax (which would compute a wrong ICMS credit)."""
        res_items = (
            "nfe",
            "samples",
            "v4_0",
            "leiauteNFe",
            "35180834128745000152550010000474281920007498-nfe.xml",
        )
        resource_path = "/".join(res_items)
        nfe_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        xml = nfe_stream.read().decode()
        # Replace the first ICMS00 node with an ICMS20 (base reduction).
        # pICMS 7.00 + 33.33% reduction is unlikely to pre-exist -> forces
        # the create-if-not-found branch.
        icms20 = (
            "<ICMS20>"
            "<orig>0</orig><CST>20</CST><modBC>3</modBC>"
            "<pRedBC>33.33</pRedBC><vBC>33.73</vBC>"
            "<pICMS>7.00</pICMS><vICMS>2.36</vICMS>"
            "</ICMS20>"
        )
        xml = re.sub(r"<ICMS00>.*?</ICMS00>", icms20, xml, count=1, flags=re.S)

        existing = self.env["l10n_br_fiscal.tax"].search(
            [
                ("tax_group_id", "=", self.env.ref("l10n_br_fiscal.tax_group_icms").id),
                ("percent_amount", "=", 7.0),
                ("percent_reduction", "=", 33.33),
            ]
        )
        self.assertFalse(existing, "test precondition: reduced tax must not exist")

        binding = TnfeProc.from_xml(xml)
        nfe = self.env["l10n_br_fiscal.document"].import_binding_nfe(
            binding, edoc_type="in", dry_run=False
        )
        created = self.env["l10n_br_fiscal.tax"].search(
            [
                ("tax_group_id", "=", self.env.ref("l10n_br_fiscal.tax_group_icms").id),
                ("percent_amount", "=", 7.0),
                ("percent_reduction", "=", 33.33),
            ]
        )
        self.assertTrue(created, "reduced ICMS tax was not created on import")
        line = nfe.fiscal_line_ids[0]
        self.assertEqual(line.icms_tax_id, created)
        self.assertEqual(line.icms_tax_id.percent_reduction, 33.33)

    def test_import_out_nfe(self):
        "(can be useful after an ERP migration)"
