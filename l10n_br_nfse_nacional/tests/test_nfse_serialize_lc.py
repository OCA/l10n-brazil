# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo.exceptions import UserError

from .test_nfse_serialize import TestNfseSerialize


class TestNfseExportLC(TestNfseSerialize):
    @classmethod
    def setUpClass(cls):
        nfse_list = [
            {
                "record_ref": "l10n_br_nfse_nacional.demo_nfse_lc",
                "xml_file": "dps-regime-normal.xml",
            }
        ]
        super().setUpClass(nfse_list)

    def _xml(self):
        """Serializing the document is what declares its service."""
        return self.nfse_list[0]["nfse"]._serialize([])[0].to_xml()

    def test_serialize_xml(self):
        for nfse_data in self.nfse_list:
            diff = self.serialize_xml(nfse_data)
            self.assertEqual(len(diff), 0, diff)

    def test_tot_trib_uses_percent_group(self):
        """Outside Simples Nacional the burden goes in pTotTrib, never indTotTrib.

        Informing indTotTrib or pTotTribSN is what the national environment
        rejects with E0713.
        """
        xml = self._xml()
        self.assertIn("<pTotTrib>", xml)
        self.assertNotIn("<pTotTribSN>", xml)
        self.assertNotIn("<indTotTrib>", xml)
        self.assertNotIn("<vTotTrib", xml)

    def test_dps_key_is_composed_from_the_document(self):
        """The DPS key is composed by the module, never typed by hand.

        Without it the Id of infDPS comes out empty, the reference of the
        signature points to nothing and the DPS is refused by the schema.
        """
        nfse = self.nfse_list[0]["nfse"]
        nfse.document_serie = "00007"
        nfse.document_number = "2"
        nfse.document_key = False
        nfse._nfse_nacional_generate_key()
        self.assertEqual(len(nfse.document_key), 42)
        self.assertTrue(nfse.document_key.endswith("2".zfill(15)))
        self.assertEqual(nfse.nfse10_Id, f"DPS{nfse.document_key}")

    def test_send_refuses_an_invalid_xml_out_loud(self):
        """A pending schema error must stop the send with a message.

        Skipping in silence left the user pressing Send with nothing happening:
        no state change, no message in the chatter, no error on screen.
        """
        nfse = self.nfse_list[0]["nfse"]
        nfse.xml_error_message = "erro de esquema deixado de proposito"
        with self.assertRaises(UserError):
            nfse._eletronic_document_send()

    def test_paliq_stays_out_of_trib_mun(self):
        """pAliq is never exported, even with an ISSQN rate on the line.

        The ADN takes the rate from the municipal parameters and refuses an
        informed rate in cases such as E0625.
        """
        self.nfse_list[0]["nfse"].fiscal_line_ids.issqn_percent = 2.5
        xml = self._xml()
        self.assertIn("<tribMun>", xml)
        # <pAliq> itself: <pAliqPis> and <pAliqCofins> are tributacaoFederal
        self.assertIsNone(re.search(r"<pAliq[ >/]", xml))

    def test_empty_groups_are_still_declared(self):
        """The DPS declares its groups even when they hold no value.

        vDescCondIncond and tribFed are optional in the leiaute, so a
        stacking algorithm that prunes empty groups drops them: the DPS then
        differs from the one the ADN produces, and installing l10n_br_nfe
        next to this module used to be enough to trigger it because both
        stack on the same l10n_br_fiscal.document model.
        """
        xml = self._xml()
        self.assertIn("<vDescCondIncond", xml)
        self.assertIn("<tribFed>", xml)
        self.assertIn("<piscofins>", xml)

    def test_dhemi_matches_local_timezone(self):
        nfse = self.nfse_list[0]["nfse"]
        self.assertEqual(nfse.nfse10_dhEmi, "2023-09-09T09:42:06-03:00")
