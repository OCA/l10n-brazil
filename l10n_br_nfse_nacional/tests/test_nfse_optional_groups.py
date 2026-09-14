# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import unittest

from odoo.tests import TransactionCase, tagged

from .common import set_provedor_nacional


# The export builds the remaining spec models on the fly, which must not happen
# inside an at_install test transaction: it would roll back their tables.
@tagged("post_install", "-at_install")
class TestNfseOptionalGroups(TransactionCase):
    """What the DPS may not carry: a masked NBS code and an empty group.

    Both were found comparing a real NFS-e issued through the national web
    emitter against the one this module builds for the same taker and the same
    amount.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.document = cls.env.ref(
            "l10n_br_nfse_nacional.demo_nfse_lc", raise_if_not_found=False
        )
        if not cls.document:
            raise unittest.SkipTest("l10n_br_nfse_nacional demo data is not installed")
        set_provedor_nacional(cls.document)
        cls.line = cls.document.fiscal_line_ids[0]

    def _prepare(self):
        """Declare the single service of the DPS, as the export does."""
        self.document._prepare_nfse10_service()
        return self.document

    def test_the_nbs_code_goes_out_without_its_mask(self):
        """The catalog stores "1.2001.50.00" for display; cNBS wants 9 digits."""
        nbs = self.env["l10n_br_fiscal.nbs"].create(
            {"name": "Industrial machinery maintenance", "code": "1.2001.50.00"}
        )
        self.line.nbs_id = nbs
        self.assertEqual(self._prepare().nfse10_cNBS, "120015000")

    def test_an_unmasked_nbs_code_is_sent_as_it_is(self):
        nbs = self.env["l10n_br_fiscal.nbs"].create(
            {"name": "Service with no mask", "code": "222222222"}
        )
        self.line.nbs_id = nbs
        self.assertEqual(self._prepare().nfse10_cNBS, "222222222")

    def test_without_an_nbs_the_tag_is_left_out(self):
        self.line.nbs_id = False
        self.assertFalse(self._prepare().nfse10_cNBS)
