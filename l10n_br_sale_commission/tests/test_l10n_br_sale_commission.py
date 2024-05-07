# Copyright (C) 2022 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import dateutil.relativedelta

from odoo import fields
from odoo.tests import SavepointCase


class TestL10nBrSalesCommission(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_order = cls.env.ref("l10n_br_sale_commission.so_commission_br")
        cls.advance_inv_model = cls.env["sale.advance.payment.inv"]
        cls.settle_model = cls.env["sale.commission.settlement"]
        cls.make_settle_model = cls.env["sale.commission.make.settle"]
        cls.make_inv_model = cls.env["sale.commission.make.invoice"]
        # A criação da Comissão valida se o Diário
        # usado pertence a mesma empresa.
        # TODO - erro q acontece apenas no teste não na tela
        #  o campo default traz um Diário de outra empresa
        cls.journal = cls.env["account.journal"].search(
            [
                ("type", "=", "purchase"),
                ("company_id", "=", cls.sale_order.company_id.id),
            ],
            limit=1,
        )

    def test_commission_config(self):
        config = self.env["res.config.settings"].create(
            {
                "commission_document_type_id": self.env.ref(
                    "l10n_br_fiscal.document_55"
                ).id,
                "commission_gen_br_fiscal_doc": False,
            }
        )
        config.execute()
        config._onchange_commission_document_type_id()
        config._onchange_commission_gen_br_fiscal_doc()

    def test_commission_config_wo_doc_type(self):
        config = self.env["res.config.settings"].create(
            {
                "commission_document_type_id": False,
                "commission_gen_br_fiscal_doc": False,
            }
        )
        config.execute()
        config._onchange_commission_document_type_id()
        config._onchange_commission_gen_br_fiscal_doc()

    def test_sale_order_commission_br(self):
        """
        Test Brazilian Commission
        """
        sale_order = self.sale_order
        agent_id = self.env.ref("sale_commission.res_partner_tiny_sale_agent")
        commission_id = self.env.ref("sale_commission.demo_commission")

        self.env["sale.order.line.agent"].create(
            {
                "agent_id": agent_id.id,
                "commission_id": commission_id.id,
                "object_id": sale_order.order_line[0].id,
            }
        )

        sale_order.action_confirm()
        self.assertEqual(len(sale_order.invoice_ids), 0)

        for picking in sale_order.picking_ids:
            for ml in picking.move_lines:
                ml.quantity_done = ml.product_qty
            picking.button_validate()

        payment = self.advance_inv_model.create(
            {
                "advance_payment_method": "delivered",
            }
        )
        context = {
            "active_model": "sale.order",
            "active_ids": [sale_order.id],
            "active_id": sale_order.id,
        }
        payment.with_context(context).create_invoices()
        self.assertNotEqual(len(sale_order.invoice_ids), 0)
        for invoice in sale_order.invoice_ids:
            invoice.flush()
            invoice.action_post()
            self.assertEqual(invoice.state, "posted")

        wizard = self.make_settle_model.create(
            {
                "date_to": (
                    fields.Datetime.from_string(fields.Datetime.now())
                    + dateutil.relativedelta.relativedelta(months=1)
                )
            }
        )

        settlements = self.settle_model.search(
            [
                ("state", "=", "settled"),
            ]
        )

        wizard.action_settle()

        settlements = self.settle_model.search(
            [
                ("state", "=", "settled"),
            ]
        )

        self.assertEqual(len(settlements), 1, "Settlements not was created.")

        # Invoice Wizard
        wizard_obj = self.make_inv_model
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard_values.get("commission_document_type_id")
        wizard_values.get("fiscal_operation_id")

        # TODO - por algum motivo aqui no teste o campo do Diário
        #  está vindo de uma outra empresa e por isso o metodo
        #  não encontra os settlement referente, o erro não
        #  acontece na tela.
        settlement_product_id = self.env.ref("product.expense_product")
        wizard_values.update(
            {
                "journal_id": self.journal.id,
                "product_id": settlement_product_id.id,
            }
        )
        wizard = wizard_obj.create(wizard_values)

        # Quick test onchange doc type
        wizard._onchange_commission_document_type_id()

        wizard.button_create()

        settlements = self.settle_model.search([("state", "=", "invoiced")])
        for settlement in settlements:
            self.assertNotEqual(
                len(settlement.invoice_id),
                0,
                "Settlements need to be in Invoiced State.",
            )
            # TODO: test fiscal_document_id in the future?
            # self.assertEqual(
            #     settlement.invoice_id.fiscal_document_id.document_type_id.id,
            #     wizard_values.get("commission_document_type_id"),
            #     "Fiscal Document with wrong Fiscal Document Type.",
            # )
            # self.assertEqual(
            #     settlement.invoice_id.fiscal_document_id.fiscal_operation_id.id,
            #     wizard_values.get("fiscal_operation_id"),
            #     "Fiscal Document with wrong Fiscal Operation.",
            # )
            for line in settlement.invoice_id.invoice_line_ids:
                self.assertEqual(
                    line.product_id.id,
                    settlement_product_id.id,
                    "Fiscal Document with wrong Product.",
                )
