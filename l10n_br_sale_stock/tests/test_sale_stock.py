# Copyright 2020 KMEE
# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.l10n_br_stock_account.tests.tools import (
    create_br_journal_and_set_fiscal_ops,
)
from odoo.addons.stock_picking_invoicing.tests.tools import (
    create_with_form_inv_onshipping,
    create_with_form_return_picking,
)

from .common import TestBRSaleStockPckInvCommon


@tagged("post_install", "-at_install")
class TestSaleStock(TestBRSaleStockPckInvCommon):
    """Test the l10n_br_sale_stock module.
    The parent classes create the company used by the tests (company_1_data)
    and all the data they need -- partners, products, fiscal operations and
    chart of accounts -- so the tests are independent from demo data.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_01_sale_stock_invoicing_and_return(self):
        """Fatura criada do Picking do Pedido de Vendas e a devolução dele.
        A Fatura é criada do Picking pelo Wizard (o caso Brasileiro precisa
        gerar o Documento Fiscal) e as Linhas da Fatura ficam ligadas às Linhas
        do Pedido de Vendas. Em seguida é feita a devolução do Pedido
        (out_refund), que recebe a Operação Fiscal de retorno ("Devolução de
        Venda", ver `run_picking_devolution`) e também precisa ser criada com o
        Documento Fiscal e com valor.
        """
        # 1) Picking do Pedido e Fatura criada dele
        so = self.sale_order_br_1
        so.action_confirm()
        self.assertTrue(
            so.picking_ids,
            'Sale Stock: no picking created for "invoice on '
            'delivery" storable products',
        )
        self.assertEqual(len(so.picking_ids), 1)
        so.picking_ids.set_to_be_invoiced()
        picking = so.picking_ids
        # Only the line of Type Product
        self.assertEqual(picking.invoice_state, "2binvoiced")
        self.picking_move_state(picking)
        invoice = create_with_form_inv_onshipping(self.env, picking)
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertEqual(invoice.move_type, "out_invoice")
        for line in invoice.invoice_line_ids:
            self.assertIn(line.sale_line_ids, so.order_line)
        # O caso Brasileiro precisa gerar o Documento Fiscal
        self.assertTrue(
            invoice.fiscal_document_id,
            "Brazilian case should has Fiscal Document.",
        )

        # 2) Devolução do Pedido de Vendas (out_refund)
        # A Operação Fiscal de retorno precisa de um Diário para a Fatura de
        # devolução ser criada (é um documento de Venda/out_refund)
        create_br_journal_and_set_fiscal_ops(
            self.env,
            so.company_id,
            so.fiscal_operation_id.return_fiscal_operation_id,
        )

        picking_devolution = self.run_picking_devolution(picking)
        invoice_devolution = create_with_form_inv_onshipping(
            self.env, picking_devolution
        )
        self.assertEqual(invoice_devolution.move_type, "out_refund")
        self.assertTrue(
            invoice_devolution.fiscal_document_id,
            "Brazilian Refund should has Fiscal Document.",
        )
        # A quantidade devolvida pelo Wizard de devolução não é a mesma da
        # Fatura original (o fixture tem entrega/retorno parcial), por isso o
        # que se verifica é que a devolução foi faturada com valor.
        self.assertGreater(
            invoice_devolution.amount_total,
            0.0,
            "Brazilian Refund Invoice should have a value.",
        )

    def test_02_compatible_with_international_case(self):
        """
        Test compatibility with international cases or
        without Fiscal Operation.
        """
        so_international = self.sale_order_1
        so_international.action_confirm()
        picking = so_international.picking_ids
        self.picking_move_state(picking)
        # Caso Internacional/Comercial: sem Operação Fiscal
        picking.fiscal_operation_id = False
        invoice = create_with_form_inv_onshipping(self.env, picking)
        invoice.action_post()
        self.assertFalse(
            invoice.fiscal_document_id,
            "International case should not has Fiscal Document.",
        )
        picking_devolution = create_with_form_return_picking(self.env, picking)
        invoice_devolution = create_with_form_inv_onshipping(
            self.env, picking_devolution
        )
        self.assertFalse(
            invoice_devolution.fiscal_document_id,
            "International case should not has Fiscal Document.",
        )

    def test_03_synchronize_sale_partner_shipping_in_stock_picking(self):
        """
        Test that when partner_shipping_id is changed after the order is
        confirmed, the related stock.picking records get their partner_id
        updated (write override on sale.order).
        """
        so = self.sale_order_br_2
        so.action_confirm()
        picking = so.picking_ids
        self.assertTrue(picking, "No picking created for storable product")
        # Change shipping partner after confirmation
        so.partner_shipping_id = self.partner_stock_1_delivery_address
        self.assertEqual(so.partner_shipping_id, picking.partner_id)

    def test_04_grouped_sale_orders(self):
        """
        Test the grouping of Pickings from different Sale Orders (and one
        without Sale Order) in the same Invoice, joining the manual additional
        data of the Sale Orders (see _build_invoice_values_from_pickings).
        """
        so_1 = self.sale_order_br_1
        so_1.action_confirm()
        picking_1 = so_1.picking_ids
        self.picking_move_state(picking_1)

        so_2 = self.sale_order_br_2
        so_2.action_confirm()
        picking_2 = so_2.picking_ids
        self.picking_move_state(picking_2)

        so_3 = self.sale_order_br_3
        so_3.action_confirm()
        picking_3 = so_3.picking_ids
        self.picking_move_state(picking_3)

        picking_4 = self.picking_out_1
        # Moves sem `sale_line_id` não entram no dict fiscal do Pedido:
        # `_get_new_picking_values` só usa os dados fiscais do Pedido quando
        # o move tem `sale_line_id`; sem ele os valores do core são mantidos.
        values = picking_4.move_ids._get_new_picking_values()
        self.assertFalse(values.get("fiscal_operation_id"))
        self.assertTrue(values, "Core values should be kept.")
        picking_4.set_to_be_invoiced()
        self.picking_move_state(picking_4)

        invoice = create_with_form_inv_onshipping(
            self.env, picking_1 | picking_2 | picking_3 | picking_4
        )
        # Com mais de um Pedido de Vendas os dados adicionais manuais são
        # juntados (sem repetir) no dicionário da Fatura
        invoice_from_sale = invoice.filtered(
            lambda inv: inv.invoice_line_ids.sale_line_ids
        )
        self.assertTrue(invoice_from_sale, "No Invoice created from Sale Orders.")
        for inv in invoice_from_sale:
            self.assertEqual(
                inv.manual_customer_additional_data,
                "Manual Customer Additional Data",
            )
            self.assertEqual(
                inv.manual_fiscal_additional_data,
                "Manual Fiscal Additional Data",
            )

    def test_05_partner_invoice_id(self):
        """A Fatura criada do Picking usa o `partner_invoice_id` do Pedido.
        Dois casos: Pedido com parceiro de faturamento diferente do parceiro do
        Picking (Endereço de Entrega) e Pedido com um Endereço de Entrega
        informado no `partner_invoice_id` -- nos dois a Fatura segue o que está
        no Pedido de Vendas.
        """
        # 1) Parceiro de faturamento diferente do parceiro do Picking
        so = self.sale_order_br_4
        so.action_confirm()
        picking = so.picking_ids
        self.picking_move_state(picking)
        invoice = create_with_form_inv_onshipping(self.env, picking)
        # O parceiro da Fatura é o partner_invoice_id do Pedido, mesmo sendo
        # diferente do parceiro do Picking (endereço de entrega)
        self.assertEqual(invoice.partner_id, so.partner_invoice_id)

        # 2) `partner_invoice_id` é um endereço de entrega
        so = self.sale_order_br_5
        so.action_confirm()
        picking = so.picking_ids
        self.picking_move_state(picking)
        invoice = create_with_form_inv_onshipping(self.env, picking)
        # Caso onde o partner_invoice_id é um endereço de entrega: a Fatura
        # segue o que está no Pedido
        self.assertEqual(invoice.partner_id, so.partner_invoice_id)

    def test_06_default_fiscal_operation_comes_from_sale_order(self):
        """A Operação Fiscal padrão do Picking vem do Pedido de Vendas.
        - Pedido sem Operação Fiscal: mantém a decisão do super;
        - Pedido com Operação Fiscal diferente da decidida pelo super: usa a
          do Pedido (ver `_get_default_fiscal_operation`);
        - Pedido com a MESMA Operação Fiscal do super: mantém.
        """
        # Pedido sem Operação Fiscal (caso internacional/comercial)
        so_international = self.sale_order_1
        so_international.action_confirm()
        picking = so_international.picking_ids
        picking.fiscal_operation_id = False
        self.assertFalse(so_international.fiscal_operation_id)
        self.assertFalse(picking._get_default_fiscal_operation())

        # Pedido com Operação Fiscal: a Operação Fiscal do Pedido é usada
        so = self.sale_order_br_2
        so.action_confirm()
        picking = so.picking_ids
        self.assertEqual(
            picking._get_default_fiscal_operation(), so.fiscal_operation_id
        )

        # Quando a decisão do super já é a Operação Fiscal do Pedido
        picking.picking_type_id.fiscal_operation_id = so.fiscal_operation_id
        self.assertEqual(
            picking._get_default_fiscal_operation(), so.fiscal_operation_id
        )
