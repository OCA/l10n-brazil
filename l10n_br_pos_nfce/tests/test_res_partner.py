# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestNFCeResPartner(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner_id = self.env.ref("l10n_br_base.res_partner_kmee")
        self.partner_id.is_anonymous_consumer = True

    def test_compute_fields(self):
        self.partner_id._compute_nfe40_ender()

        self.assertEqual(self.partner_id.nfe40_xLgr, "")
        self.assertEqual(self.partner_id.nfe40_nro, "")
        self.assertEqual(self.partner_id.nfe40_xCpl, "")
        self.assertEqual(self.partner_id.nfe40_xBairro, "")
        self.assertEqual(self.partner_id.nfe40_cMun, "")
        self.assertEqual(self.partner_id.nfe40_xMun, "")
        self.assertEqual(self.partner_id.nfe40_UF, "")
        self.assertEqual(self.partner_id.nfe40_cPais, "")
        self.assertEqual(self.partner_id.nfe40_xPais, "")
