# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import SavepointCase


class L10nBrSaleInvoicePlanBaseTest(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.so_service = cls.env.ref(
            "l10n_br_sale_invoice_plan.lc_so_invoice_plan_service_br"
        )
        cls.sl_service_1 = cls.env.ref(
            "l10n_br_sale_invoice_plan.lc_sl_invoice_plan_service_br_1_1"
        )

        cls.fsc_op_sale = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.fsc_op_line_serv = cls.env.ref("l10n_br_fiscal.fo_venda_servico")

    def test_l10n_br_sale_invoice_plan_service(self):
        ctx = {
            "active_id": self.so_service.id,
            "active_ids": [self.so_service.id],
            "all_remain_invoices": False,
            "default_company_id": self.company.id,
        }

        self.so_service.action_confirm()
        make_wizard = self.env["sale.make.planned.invoice"].create({})
        make_wizard.with_context(ctx).create_invoices_by_plan()
        invoices = self.so_service.invoice_ids
        line = invoices[0].invoice_line_ids[0]
        self.assertEqual(len(invoices), 1, "Only 1 invoice should be created")
        self.assertEqual(
            line.quantity,
            line.fiscal_quantity,
            "The fiscal_quantity must be equal the quantity",
        )
        self.assertTrue(line.fiscal_operation_id)
        self.assertTrue(line.fiscal_tax_ids)
        self.assertTrue(line.invoice_line_tax_ids)
