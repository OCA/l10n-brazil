# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestNfseOptionalGroups(TransactionCase):
    """What the DPS may not carry: a masked NBS code and an empty group.

    Both were found comparing a real NFS-e issued through the national web
    emitter against the one this module builds for the same taker and the same
    amount.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.line = cls.env.ref("l10n_br_nfse_nacional.demo_nfse_lc").fiscal_line_ids[0]

    def test_the_nbs_code_goes_out_without_its_mask(self):
        """The catalog stores "1.2001.50.00" for display; cNBS wants 9 digits."""
        nbs = self.env["l10n_br_fiscal.nbs"].create(
            {"name": "Industrial machinery maintenance", "code": "1.2001.50.00"}
        )
        self.line.nbs_id = nbs
        self.assertEqual(self.line.nfse10_cNBS, "120015000")

    def test_an_unmasked_nbs_code_is_sent_as_it_is(self):
        nbs = self.env["l10n_br_fiscal.nbs"].create(
            {"name": "Service with no mask", "code": "222222222"}
        )
        self.line.nbs_id = nbs
        self.assertEqual(self.line.nfse10_cNBS, "222222222")

    def test_without_an_nbs_the_tag_is_left_out(self):
        self.line.nbs_id = False
        self.assertFalse(self.line.nfse10_cNBS)

    def test_the_discount_group_is_absent_when_there_is_no_discount(self):
        """Pointing the group at the line always serializes an empty tag."""
        self.line.write({"discount_value": 0.0, "issqn_desc_cond_amount": 0.0})
        self.assertFalse(self.line.nfse10_vDescCondIncond)

    def test_an_unconditional_discount_brings_the_group_back(self):
        self.line.discount_value = 10.0
        self.assertEqual(self.line.nfse10_vDescCondIncond, self.line)
        self.assertEqual(self.line.nfse10_vDescIncond, "10.00")

    def test_a_conditional_discount_brings_the_group_back(self):
        self.line.write({"discount_value": 0.0, "issqn_desc_cond_amount": 7.5})
        self.assertEqual(self.line.nfse10_vDescCondIncond, self.line)
        self.assertEqual(self.line.nfse10_vDescCond, "7.50")
