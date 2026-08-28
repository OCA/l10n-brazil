# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


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
        self.line.issqn_eligibility = "4"
        self.assertEqual(self.line.nfse10_tribISSQN, "3")

        self.line.issqn_eligibility = "5"
        self.assertEqual(self.line.nfse10_tribISSQN, "2")

        self.line.issqn_eligibility = "1"
        self.assertEqual(self.line.nfse10_tribISSQN, "1")

    def test_a_new_line_is_taxable_and_not_exempt(self):
        """A new line is born taxable: "Exigivel" is the common case of a
        service note, and the DPS carries tribISSQN 1."""
        line = self.env["l10n_br_fiscal.document.line"].new({})
        self.assertEqual(line.issqn_eligibility, "1")
        self.assertEqual(line.nfse10_tribISSQN, "1")

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
