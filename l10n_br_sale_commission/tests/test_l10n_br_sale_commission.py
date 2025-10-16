# Copyright (C) 2022-Today - Akretion (<http://www.akretion.com>).
# @author Renato Lima <renato.lima@akretion.com.br>
# @author Magno Costa <magno.costa@akretion.com.br>
# Copyright (C) 2025 - Engenere (<http://www.engenere.one>).
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import Command
from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestL10nBrSalesCommission(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.commission = cls.env["commission"].create(
            {
                "name": "Commission 10%",
                "commission_type": "fixed",
                "fix_qty": 10.0,
                "amount_base_type": "gross_amount",
                "settlement_type": "sale_invoice",
            }
        )
        cls.agent = cls.env["res.partner"].create(
            {
                "name": "Sales Agent",
                "company_id": cls.company.id,
                "agent": True,
                "commission_id": cls.commission.id,
                "settlement": "monthly",
            }
        )
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "BR Customer",
                "company_id": cls.company.id,
                "agent_ids": [Command.set(cls.agent.ids)],
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Commissioned Service",
                "list_price": 500.0,
                "type": "service",
            }
        )

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

    @classmethod
    def _create_sale_order_with_commission(cls):
        """Build a simple sale order linked to the default agent/commission."""

        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.customer
        sale_form.pricelist_id = cls.env.ref("product.list0")
        sale_form.fiscal_operation_id = cls.env.ref("l10n_br_fiscal.fo_venda")
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product
            line_form.product_uom_qty = 2
            line_form.price_unit = cls.product.list_price
            line_form.fiscal_operation_id = cls.env.ref("l10n_br_fiscal.fo_venda")
            line_form.fiscal_operation_line_id = cls.env.ref(
                "l10n_br_fiscal.fo_venda_venda"
            )

        sale_order = sale_form.save()
        sale_order.recompute_lines_agents()

        return sale_order

    def test_sale_order_commission_br(self):
        """Test Brazilian Commission"""

        sale_order = self._create_sale_order_with_commission()
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

    def test_sale_order_commission_override_persists_on_invoice(self):
        """Validate custom agent/commission stay on invoice."""

        sale_order = self._create_sale_order_with_commission()
        override_commission = self.env["commission"].create(
            {
                "name": "Commission 15%",
                "commission_type": "fixed",
                "fix_qty": 15.0,
                "amount_base_type": "gross_amount",
                "settlement_type": "sale_invoice",
            }
        )
        override_agent = self.env["res.partner"].create(
            {
                "name": "Sales Agent Override",
                "company_id": self.company.id,
                "agent": True,
                "commission_id": override_commission.id,
                "settlement": "monthly",
            }
        )

        order_line_agent = sale_order.order_line.agent_ids
        self.assertTrue(order_line_agent)
        self.assertEqual(order_line_agent.commission_id, self.commission)
        self.assertEqual(order_line_agent.agent_id, self.agent)

        order_line_agent.commission_id = override_commission
        order_line_agent.agent_id = override_agent

        sale_order.action_confirm()
        sale_order._create_invoices(final=True)
        invoice = sale_order.invoice_ids

        invoice_line_agents = invoice.invoice_line_ids.filtered(
            lambda line: line.product_id == self.product
        ).agent_ids
        self.assertTrue(invoice_line_agents)
        self.assertEqual(invoice_line_agents.commission_id, override_commission)
        self.assertEqual(invoice_line_agents.agent_id, override_agent)
