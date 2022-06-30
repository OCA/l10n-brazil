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

    def test_sale_order_commission_br(self):
        """
        Test Brazilian Commission
        """
        sale_order = self.sale_order
        sale_order.action_confirm()
        self.assertEqual(len(sale_order.invoice_ids), 0)
        payment = self.advance_inv_model.create(
            {
                "advance_payment_method": "all",
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
            invoice.action_invoice_open()
            self.assertEqual(invoice.state, "open")

        wizard = self.make_settle_model.create(
            {
                "date_to": (
                    fields.Datetime.from_string(fields.Datetime.now())
                    + dateutil.relativedelta.relativedelta(months=1)
                )
            }
        )
        wizard.action_settle()

        settlements = self.settle_model.search([("state", "=", "settled")])
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
        wizard_values.update({"journal": self.journal.id})
        wizard = wizard_obj.create(wizard_values)
        wizard.button_create()

        settlements = self.settle_model.search([("state", "=", "invoiced")])
        for settlement in settlements:
            self.assertNotEqual(
                len(settlement.invoice), 0, "Settlements need to be in Invoiced State."
            )
            self.assertEqual(
                settlement.invoice.fiscal_document_id.document_type_id.id,
                wizard_values.get("commission_document_type_id"),
                "Fiscal Document with wrong Fiscal Document Type.",
            )
            self.assertEqual(
                settlement.invoice.fiscal_document_id.fiscal_operation_id.id,
                wizard_values.get("fiscal_operation_id"),
                "Fiscal Document with wrong Fiscal Operation.",
            )
            for line in settlement.invoice.invoice_line_ids:
                self.assertEqual(
                    line.product_id.id,
                    wizard_values.get("product"),
                    "Fiscal Document with wrong Product.",
                )
