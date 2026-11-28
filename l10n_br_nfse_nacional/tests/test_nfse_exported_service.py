# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from nfelib.nfse.bindings.v1_0.dps_v1_01 import Dps

from odoo.tests import TransactionCase, tagged

from .common import set_provedor_nacional


class TestNfseExportedService(TransactionCase):
    """The DPS declares how the ISSQN falls on the service.

    1 is taxable, 2 is immunity, 3 is export of service and 4 is no incidence
    (TSTribISSQN of the national layout).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.line = cls.env.ref("l10n_br_nfse_nacional.demo_nfse_lc").fiscal_line_ids[0]
        cls.abroad = cls.env["res.partner"].create(
            {
                "name": "Tomador no exterior",
                "is_company": True,
                "country_id": cls.env.ref("base.es").id,
            }
        )

    def test_an_exported_service_is_not_declared_as_taxable(self):
        # The indicator describes the single service of the DPS, so it is
        # prepared on the fiscal document from the line right before the
        # export, like the other groups of the service.
        document = self.line.document_id
        for eligibility, expected in (
            ("4", "3"),
            ("5", "2"),
            ("1", "1"),
        ):
            self.line.issqn_eligibility = eligibility
            document._prepare_nfse10_service()
            self.assertEqual(document.nfse10_tribISSQN, expected)

    def test_a_new_line_is_taxable_and_not_exempt(self):
        """A new line is born taxable: "Exigivel" is the common case of a
        service note, and the DPS carries tribISSQN 1."""
        document = self.env["l10n_br_fiscal.document"].new({})
        line = self.env["l10n_br_fiscal.document.line"].new({})
        self.assertEqual(line.issqn_eligibility, "1")
        self.assertEqual(document._nfse10_trib_issqn_code(line), "1")

    def test_a_taker_abroad_carries_its_own_tax_number(self):
        self.abroad.vat = "ESA58818501"
        self.assertEqual(self.abroad.nfse10_NIF, "ESA58818501")
        self.assertFalse(self.abroad.nfse10_cNaoNIF)

    def test_a_taker_abroad_without_a_tax_number_says_why(self):
        self.abroad.nif_motive_absence = "2"
        self.assertFalse(self.abroad.nfse10_NIF)
        self.assertEqual(self.abroad.nfse10_cNaoNIF, "2")

        self.abroad.nif_motive_absence = False
        self.assertEqual(self.abroad.nfse10_cNaoNIF, "1")


@tagged("post_install", "-at_install")
class TestNfseTakerAbroad(TransactionCase):
    """A taker abroad is declared with the address abroad (endExt)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.abroad = cls.env["res.partner"].create(
            {
                "name": "Tomador no exterior",
                "is_company": True,
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.us = cls.env["res.partner"].create(
            {
                "name": "Customer in New York",
                "is_company": True,
                "country_id": cls.env.ref("base.us").id,
                "state_id": cls.env.ref("base.state_us_27").id,
                "city": "New York",
                "zip": "10001",
                "street_name": "Broadway",
                "street_number": "1500",
                "vat": "123456789",
            }
        )

    def _serialized_dps(self, partner):
        document = self.env.ref("l10n_br_nfse_nacional.demo_nfse_lc")
        set_provedor_nacional(document)
        document.partner_id = partner
        document.fiscal_line_ids[0].issqn_eligibility = "4"
        xml = document._serialize([])[0].to_xml()
        return document, xml

    def test_a_taker_abroad_is_declared_with_the_address_abroad(self):
        """endNac asks for the municipality code, which a taker abroad does not
        have (E0242, EM033): the DPS carries endExt instead."""
        _document, xml = self._serialized_dps(self.us)
        self.assertEqual(Dps.schema_validation(xml), [])
        self.assertIn("<endExt>", xml)
        self.assertNotIn("<endNac>", xml)
        self.assertIn("<cPais>US</cPais>", xml)
        self.assertIn("<cEndPost>10001</cEndPost>", xml)
        self.assertIn("<xCidade>New York</xCidade>", xml)
        self.assertIn("<xEstProvReg>New York</xEstProvReg>", xml)
        self.assertIn("<tribISSQN>3</tribISSQN>", xml)

    def test_an_address_abroad_without_number_nor_district(self):
        self.us.write({"street_number": False, "district": False})
        _document, xml = self._serialized_dps(self.us)
        self.assertEqual(Dps.schema_validation(xml), [])
        self.assertIn("<nro>S/N</nro>", xml)

    def test_the_state_completes_the_address_abroad(self):
        """The group needs the state or province: it appears when it is filled."""
        self.us.state_id = False
        self.assertFalse(self.us.nfse10_endExt)
        self.us.state_id = self.env.ref("base.state_us_27")
        self.assertEqual(self.us.nfse10_endExt, self.us)

    def test_a_taker_abroad_without_address_leaves_the_group_out(self):
        self.assertFalse(self.abroad.nfse10_end)
        self.assertFalse(self.abroad.nfse10_endExt)
        self.assertFalse(self.abroad.nfse10_endNac)

    def test_a_national_taker_keeps_endnac(self):
        document = self.env.ref("l10n_br_nfse_nacional.demo_nfse_lc")
        set_provedor_nacional(document)
        xml = document._serialize([])[0].to_xml()
        self.assertIn("<endNac>", xml)
        self.assertNotIn("<endExt>", xml)
