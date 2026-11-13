# Copyright 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestIcmsNoCredit(AccountMoveBRCommon):
    """A purchase for use and consumption does not take the ICMS credit.

    LC 87/1996, art. 33, I: the vendor bill of such a purchase books no ICMS
    to recover, and the ICMS stays in the cost of the line.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_data["company"].icms_regulation_id = cls.env.ref(
            "l10n_br_fiscal.tax_icms_regulation"
        )
        cls.operation_line = cls.env.ref(
            "l10n_br_fiscal.fo_compras_compras_uso_consumo"
        )

    def _purchase_move(self, number):
        return self.init_invoice(
            "in_invoice",
            products=[self.product_a],
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=self.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[self.operation_line],
            document_serie="1",
            document_number=number,
        )

    def _icms_lines(self, move):
        return move.line_ids.filtered(
            lambda line: line.tax_line_id.tax_group_id.fiscal_tax_group_id.tax_domain
            == "icms"
        )

    def test_icms_no_credit(self):
        credit_move = self._purchase_move("4997")
        self.assertTrue(
            self._icms_lines(credit_move), "without the flag the ICMS goes to recover"
        )

        self.operation_line.icms_no_credit = True
        move = self._purchase_move("4998")
        line = move.invoice_line_ids
        self.assertTrue(line.icms_value, "the purchase has ICMS")
        self.assertFalse(self._icms_lines(move))
        self.assertAlmostEqual(
            line.balance, credit_move.invoice_line_ids.balance + line.icms_value
        )
        self.assertAlmostEqual(sum(move.line_ids.mapped("balance")), 0.0)
