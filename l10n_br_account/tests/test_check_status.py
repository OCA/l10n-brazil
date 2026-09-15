# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import tagged

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_STATE_CANCEL

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestCheckStatusBR(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_normal_company_taxes()

    def _posted_invoice(self):
        invoice = self.init_invoice(
            "out_invoice",
            products=[self.product_a],
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=self.empresa_lc_document_55_serie_1,
            fiscal_operation=self.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[self.env.ref("l10n_br_fiscal.fo_venda_venda")],
        )
        invoice.action_post()
        return invoice

    def _pay(self, invoice):
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create(
            {"journal_id": self.company_data["default_journal_bank"].id}
        )._create_payments()

    def test_a_paid_invoice_the_sefaz_voided_needs_a_manual_settlement(self):
        invoice = self._posted_invoice()
        self._pay(invoice)
        self.assertEqual(invoice.payment_state, "paid")

        invoice.fiscal_document_id.state_edoc = DOCUMENT_STATE_CANCEL

        self.assertEqual(invoice._settled_moves_no_longer_valid(), invoice)

    def test_an_unpaid_invoice_the_sefaz_voided_is_left_alone(self):
        invoice = self._posted_invoice()
        self.assertEqual(invoice.payment_state, "not_paid")

        invoice.fiscal_document_id.state_edoc = DOCUMENT_STATE_CANCEL

        self.assertFalse(invoice._settled_moves_no_longer_valid())
