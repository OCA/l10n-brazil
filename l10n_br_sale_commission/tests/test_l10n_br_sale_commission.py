# Copyright (C) 2022-Today - Akretion (<http://www.akretion.com>).
# @author Renato Lima <renato.lima@akretion.com.br>
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.tests import Form, TransactionCase


class TestL10nBrSalesCommission(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_commission_config(self):
        config_form = Form(self.env["res.config.settings"])
        config_form.commission_gen_br_fiscal_doc = True
        config_form.commission_document_type_id = self.env.ref(
            "l10n_br_fiscal.document_55"
        )
        config = config_form.save()
        config.execute()

    def test_commission_config_wo_doc_type(self):
        config_form = Form(self.env["res.config.settings"])
        config_form.commission_gen_br_fiscal_doc = False
        config = config_form.save()
        config.execute()

    def _get_settlements_invoice(self):
        # Cria o Settlements
        with Form(self.env["commission.make.settle"]) as wiz_form:
            wiz_form.date_to = date.today() + relativedelta(months=1)
            wiz_form.settlement_type = "sale_invoice"
            wiz = wiz_form.save()
            wiz.action_settle()

        settlements = self.env["commission.settlement"].search(
            [
                ("state", "=", "settled"),
            ]
        )

        self.assertEqual(len(settlements), 1, "Settlements not was created.")

        # Cria a Fatura das Comissões/Settlements
        with Form(self.env["commission.make.invoice"]) as wiz_form:
            wiz = wiz_form.save()
            wiz.button_create()

        settlements = self.env["commission.settlement"].search(
            [("state", "=", "invoiced")]
        )
        for settlement in settlements:
            self.assertNotEqual(
                len(settlement.invoice_id),
                0,
                "Settlements need to be in Invoiced State.",
            )
            self.assertEqual(
                settlement.invoice_id.fiscal_document_id.document_type_id,
                self.env.ref("l10n_br_fiscal.document_SE"),
                "Fiscal Document with wrong Fiscal Document Type.",
            )
            self.assertTrue(
                settlement.invoice_id.fiscal_document_id.document_serie_id,
                "Fiscal Document withiout Document Serie.",
            )
            self.assertEqual(
                settlement.invoice_id.fiscal_document_id.fiscal_operation_id,
                self.env.ref("l10n_br_fiscal.fo_compras"),
                "Fiscal Document with wrong Fiscal Operation.",
            )
            for line in settlement.invoice_id.invoice_line_ids:
                self.assertEqual(
                    line.product_id,
                    self.env.ref("l10n_br_sale_commission.service_commission"),
                    "Fiscal Document with wrong Product.",
                )
                self.assertEqual(
                    line.settlement_id,
                    settlement,
                    "Settlement not informed in Move Line",
                )
                self.assertTrue(
                    line.fiscal_operation_id,
                    "Fiscal Operation not informed in Move Line",
                )
                self.assertTrue(
                    line.fiscal_operation_line_id,
                    "Fiscal Operation Line not informed in Move Line",
                )

                # Verifica a necessidade de rodar o onchange_fiscal_operation_id
                self.assertTrue(
                    line.fiscal_tax_ids,
                    "Fiscal Tax not informed in Move Line",
                )
                self.assertTrue(
                    line.icms_cst_id,
                    "ICMS CST not informed in Move Line",
                )
                # A Linha de Operação Fiscal 'Prestação de Serviço'
                # da Operação Fiscal 'Compras' não tem CFOP.
                # TODO: Essa Linha de OP Fiscal deveria ter CFOP?
                # self.assertTrue(
                #    line.cfop_id,
                #    "CFOP not informed in Move Line",
                # )

        return settlements.mapped("invoice_id")

    def test_sale_order_commission_br(self):
        """Test Brazilian Commission"""

        sale_order = self.env.ref("l10n_br_sale_commission.so_commission_br")
        sale_order.action_confirm()
        self.assertEqual(len(sale_order.invoice_ids), 0)
        sale_order._create_invoices(final=True)
        self.assertNotEqual(len(sale_order.invoice_ids), 0)

        invoice_with_commission = sale_order.mapped("invoice_ids")
        invoice_with_commission.action_post()
        self.assertEqual(invoice_with_commission.state, "posted")

        # Pagamento
        journal_cash = self.env["account.journal"].search(
            [("type", "=", "cash"), ("company_id", "=", self.env.company.id)],
            limit=1,
        )

        payment_register = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=invoice_with_commission.ids,
            )
        )
        payment_register.journal_id = journal_cash
        method_lines = journal_cash._get_available_payment_method_lines(
            "inbound"
        ).filtered(lambda x: x.code == "manual")
        payment_register.payment_method_line_id = method_lines[0]
        payment_register.amount = invoice_with_commission.amount_total
        payment_register.save()._create_payments()

        # Cria o Settlements
        settlement_invoice = self._get_settlements_invoice()
        self.assertEqual(settlement_invoice.move_type, "in_invoice")
        settlement_invoice.action_post()

        # Refund

        refund_invoice_with_commission = invoice_with_commission._reverse_moves(
            default_values_list=[
                {
                    "invoice_date": invoice_with_commission.invoice_date,
                }
            ]
        )
        self.assertEqual(
            invoice_with_commission.invoice_line_ids.agent_ids.agent_id,
            refund_invoice_with_commission.invoice_line_ids.agent_ids.agent_id,
        )
        refund_invoice_with_commission.invoice_line_ids.agent_ids._compute_amount()
        refund_invoice_with_commission.action_post()

        # Refund Commission to be Pay
        settlements_invoice = self._get_settlements_invoice()
        refund_settlement_invoice = settlements_invoice.filtered(
            lambda st: st.move_type == "in_refund"
        )
        self.assertEqual(
            len(refund_settlement_invoice),
            1,
            "Refund Commission Invoice was not Created.",
        )
        refund_settlement_invoice.action_post()
