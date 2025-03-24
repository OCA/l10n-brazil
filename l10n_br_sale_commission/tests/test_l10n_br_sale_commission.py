# Copyright (C) 2022 - TODAY Renato Lima - Akretion
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

    def test_sale_order_commission_br(self):
        """
        Test Brazilian Commission
        """
        sale_order = self.env.ref("l10n_br_sale_commission.so_commission_br")
        sale_order.action_confirm()
        self.assertEqual(len(sale_order.invoice_ids), 0)
        sale_order._create_invoices(final=True)
        self.assertNotEqual(len(sale_order.invoice_ids), 0)
        for invoice in sale_order.invoice_ids:
            invoice.action_post()
            self.assertEqual(invoice.state, "posted")

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
