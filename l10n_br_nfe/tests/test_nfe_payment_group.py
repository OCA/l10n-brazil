# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command, fields
from odoo.tests.common import TransactionCase


class TestNFePaymentGroup(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids += company
        cls.env.user.company_id = company
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente7_rs")
        cls.product = cls.env.ref("product.product_product_4c")

    def _create_nfe(self, operation_xmlid):
        operation = self.env.ref(operation_xmlid)
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "partner_id": self.partner.id,
                "ind_final": "0",
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "fiscal_operation_id": operation.id,
            }
        )
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": document.id,
                "company_id": document.company_id.id,
                "partner_id": document.partner_id.id,
                "fiscal_operation_type": document.fiscal_operation_type,
                "fiscal_operation_id": operation.id,
                "product_id": self.product.id,
            }
        )
        line.write(
            {
                "price_unit": 100.0,
                "fiscal_price": 100.0,
                "quantity": 2,
                "fiscal_quantity": 2,
            }
        )
        return document

    def test_filled_payment_group_is_kept(self):
        """What l10n_br_account_nfe fills is not touched."""
        document = self._create_nfe("l10n_br_fiscal.fo_venda")
        amount = document.amount_financial_total
        document.write(
            {
                "nfe40_detPag": [
                    Command.create(
                        {"nfe40_indPag": "1", "nfe40_tPag": "15", "nfe40_vPag": amount}
                    )
                ],
                "nfe40_dup": [
                    Command.create(
                        {
                            "nfe40_nDup": "001",
                            "nfe40_dVenc": "2026-11-10",
                            "nfe40_vDup": amount,
                        }
                    )
                ],
            }
        )
        document.action_document_confirm()

        self.assertEqual(document.nfe40_detPag.mapped("nfe40_tPag"), ["15"])
        self.assertEqual(
            document.nfe40_dup.mapped("nfe40_dVenc"),
            [fields.Date.to_date("2026-11-10")],
        )

    def test_sale_without_payment(self):
        """Financial operation: no payment (90) and one installment due on issue."""
        document = self._create_nfe("l10n_br_fiscal.fo_venda")
        self.assertTrue(document.amount_financial_total)
        document.action_document_confirm()

        self.assertEqual(len(document.nfe40_detPag), 1)
        self.assertEqual(document.nfe40_detPag.nfe40_tPag, "90")
        self.assertEqual(document.nfe40_detPag.nfe40_vPag, 0.0)
        self.assertEqual(len(document.nfe40_dup), 1)
        self.assertEqual(document.nfe40_dup.nfe40_nDup, "001")
        self.assertEqual(
            document.nfe40_dup.nfe40_dVenc,
            fields.Date.context_today(document, document.document_date),
        )
        self.assertAlmostEqual(
            document.nfe40_dup.nfe40_vDup, document.amount_financial_total, places=2
        )

    def test_bonus_without_installment(self):
        """Bonus generates no financial amount: no payment (90), no installment."""
        document = self._create_nfe("l10n_br_fiscal.fo_bonificacao")
        self.assertFalse(document.amount_financial_total)
        document.action_document_confirm()

        self.assertEqual(document.nfe40_detPag.mapped("nfe40_tPag"), ["90"])
        self.assertFalse(document.nfe40_dup)
