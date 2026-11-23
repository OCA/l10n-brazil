# Copyright (C) 2026 - TODAY KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase


class TestImportFreightPurchaseOperation(TransactionCase):
    """A freight service issued by the carrier (CFOP 5352, 5353, 6352, 6353)
    finds the purchase operation line of the receiver (1352, 1353, 2352, 2353).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.operation_lines = cls.env["l10n_br_fiscal.operation.line"]
        cls.purchase = cls.env.ref("l10n_br_fiscal.fo_compras")

    def test_issuer_cfop_finds_the_freight_purchase_line(self):
        expected = {
            "5352": "l10n_br_fiscal.fo_compras_transporte_industrial",
            "6352": "l10n_br_fiscal.fo_compras_transporte_industrial",
            "5353": "l10n_br_fiscal.fo_compras_transporte_comercial",
            "6353": "l10n_br_fiscal.fo_compras_transporte_comercial",
        }
        for cfop, xmlid in expected.items():
            with self.subTest(cfop=cfop):
                line = self.operation_lines._find_by_issuer_cfop(cfop, False, "in")
                self.assertEqual(line, self.env.ref(xmlid))
                self.assertEqual(line.fiscal_operation_id, self.purchase)

    def test_freight_purchase_lines_are_approved_inbound(self):
        for xmlid in (
            "l10n_br_fiscal.fo_compras_transporte_industrial",
            "l10n_br_fiscal.fo_compras_transporte_comercial",
        ):
            with self.subTest(line=xmlid):
                line = self.env.ref(xmlid)
                self.assertEqual(line.state, "approved")
                self.assertEqual(line.fiscal_operation_type, "in")
                self.assertTrue(line.cfop_internal_id)
                self.assertTrue(line.cfop_external_id)
