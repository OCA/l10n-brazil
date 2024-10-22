# Copyright (C) 2022  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import SavepointCase, tagged


@tagged("post_install", "-at_install")
class TestSaleCommissionStock(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.invoice_model = cls.env["account.invoice"]
        cls.invoice_wizard = cls.env["stock.invoice.onshipping"]
        cls.stock_picking = cls.env["stock.picking"]

        # TODO: Em uma instalção direta do modulo
        #  $ odoo -d test -i l10n_br_sale_stock --stop-after-init
        #  e depois
        #  $ odoo -d test --update=l10n_br_sale_stock --test-enable
        #  o campo do Diário não está vindo preenchido a solução e forçar
        #  preenchimento para não ter erro nos testes porem no caso dos dados
        #  demo ao testar na tela vai continuar o problema, para evita-lo é
        #  preciso instalar o l10n_br_account antes ou preencher manualmente,
        #  porém isso é um problema já que a instalação direta do modulo deve
        #  funcionar sem isso.
        #  No modulo l10n_br_sale para resolver esse problema é feito isso
        #  https://github.com/OCA/l10n-brazil/blob/12.0/l10n_br_sale/
        #  hooks.py#L35 e https://github.com/OCA/l10n-brazil/blob/12.0/
        #  l10n_br_sale/demo/fiscal_operation_simple.xml#L10 mas por algum
        #  motivo não vem carregado aqui, mesmo tendo o l10n_br_sale como
        #  dependencia.
        cls.fiscal_operation_venda = cls.env.ref("l10n_br_fiscal.fo_venda")
        if not cls.fiscal_operation_venda.journal_id:
            cls.fiscal_operation_venda.journal_id = cls.env.ref(
                "l10n_br_coa_simple.sale_journal_main_company"
            )
        cls.fiscal_operation_dev_venda = cls.env.ref(
            "l10n_br_fiscal.fo_devolucao_venda"
        )
        if not cls.fiscal_operation_dev_venda.journal_id:
            cls.fiscal_operation_dev_venda.journal_id = cls.env.ref(
                "l10n_br_coa_simple.general_journal_main_company"
            )

    def test_01_sale_commission_stock(self):
        """
        Test a SO with a product invoiced on delivery. Deliver and invoice
        the SO, then do a return
        of the picking. Check that a refund invoice is well generated.
        """
        # intial sale order
        self.so = self.env.ref(
            "l10n_br_sale_commission_stock.main_so_l10n_br_sale_commission_stock_1"
        )

        for line in self.so.order_line:
            line._onchange_product_id_fiscal()

        # confirm our standard so, check the picking
        self.so.action_confirm()
        self.assertTrue(
            self.so.picking_ids,
            'Sale Stock: no picking created for "invoice on '
            'delivery" storable products',
        )

        # validate stock.picking
        stock_picking = self.so.picking_ids

        self.env["stock.immediate.transfer"].create(
            {"pick_ids": [(4, stock_picking.id)]}
        ).process()

        self.assertEqual(stock_picking.state, "done")

        # set stock.picking to be invoiced
        self.assertTrue(
            len(self.so.picking_ids) == 1,
            "More than one stock " "picking for sale.order",
        )
        self.so.picking_ids.set_to_be_invoiced()

        # create invoice

        wizard_obj = self.invoice_wizard.with_context(
            active_ids=stock_picking.ids,
            active_model=stock_picking._name,
            active_id=stock_picking.id,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()
        domain = [("picking_ids", "=", stock_picking.id)]
        invoice = self.invoice_model.search(domain)
        self.assertEqual(stock_picking.invoice_state, "invoiced")
        self.assertIn(invoice, stock_picking.invoice_ids)

        for invoice_line in invoice.invoice_line_ids:
            self.assertEqual(
                len(invoice_line.agents), len(invoice_line.sale_line_ids.agents)
            )
            for invoice_line_agent in invoice_line.agents:
                sale_line_agent = self.env["sale.order.line.agent"].search(
                    [
                        ("object_id", "in", invoice_line.sale_line_ids.ids),
                        ("agent", "=", invoice_line_agent.agent.id),
                        ("commission", "=", invoice_line_agent.commission.id),
                    ]
                )

                self.assertTrue(
                    sale_line_agent,
                    "Invoice Line Commission infos: is not correct!",
                )
