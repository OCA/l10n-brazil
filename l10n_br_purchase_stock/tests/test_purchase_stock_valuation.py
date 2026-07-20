# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestPurchaseStockValuationNetCost(TransactionCase):
    """Fluxo PO completo com custo líquido (Art. 301 RIR/2018, CPC 16):
    PO → picking → SVL, incluindo o caso brasileiro típico de a NF ser
    lançada ANTES do recebimento (a nota acompanha a mercadoria)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company

        cls.product = cls.env.ref("product.product_product_6")
        cls.supplier = cls.env.ref("l10n_br_base.res_partner_intel")
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.fiscal_operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")

        Account = cls.env["account.account"]
        cls.account_valuation = Account.create(
            {
                "name": "Estoque (teste PO valuation)",
                "code": "TSTPOV",
                "account_type": "asset_current",
                "company_id": cls.company.id,
            }
        )
        cls.account_stock_in = Account.create(
            {
                "name": "Ponte entrada (teste PO)",
                "code": "TSTPOI",
                "account_type": "asset_current",
                "company_id": cls.company.id,
            }
        )
        cls.account_stock_out = Account.create(
            {
                "name": "Ponte saída (teste PO)",
                "code": "TSTPOO",
                "account_type": "asset_current",
                "company_id": cls.company.id,
            }
        )
        stock_journal = cls.env["account.journal"].create(
            {
                "name": "Stock Journal (teste PO)",
                "code": "TSTPJ",
                "type": "general",
                "company_id": cls.company.id,
            }
        )
        cls.product.categ_id.with_company(cls.company).write(
            {
                "property_valuation": "real_time",
                "property_cost_method": "fifo",
                "property_stock_account_input_categ_id": cls.account_stock_in.id,
                "property_stock_account_output_categ_id": cls.account_stock_out.id,
                "property_stock_valuation_account_id": cls.account_valuation.id,
                "property_stock_journal": stock_journal.id,
            }
        )

    def _make_po(self, qty=1.0, price=800.0):
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.supplier.id,
                "company_id": self.company.id,
                "fiscal_operation_id": self.fiscal_operation.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": qty,
                            "price_unit": price,
                            "product_uom": self.product.uom_id.id,
                            "name": self.product.name,
                            "fiscal_operation_id": self.fiscal_operation.id,
                            "fiscal_operation_line_id": (self.fiscal_operation_line.id),
                        },
                    )
                ],
            }
        )
        po.button_confirm()
        return po

    def _receive(self, picking, qty_done=None):
        for line in picking.move_ids.move_line_ids:
            line.qty_done = qty_done if qty_done is not None else line.reserved_uom_qty
        picking.with_context(skip_immediate=True, skip_backorder=True).button_validate()

    def test_po_receipt_net_cost(self):
        """PO → recebimento: SVL usa o custo líquido do pedido
        (Presumido: 800 − ICMS creditável)."""
        po = self._make_po()
        pol = po.order_line
        self.assertGreater(pol.icms_value, 0)
        self.assertAlmostEqual(
            pol.stock_cost_unit, pol.price_unit - pol.icms_value, places=2
        )

        picking = po.picking_ids
        self._receive(picking)
        move = picking.move_ids
        svl = move.stock_valuation_layer_ids
        self.assertAlmostEqual(svl.unit_cost, pol.stock_cost_unit, places=2)
        self.assertNotEqual(svl.unit_cost, pol.price_unit)

    def test_invoice_before_receipt_net_cost(self):
        """NF lançada ANTES do recebimento com preço diferente do PO:
        o SVL usa o custo líquido DA NF (não o do pedido) — RF-A3."""
        self.product.write({"purchase_method": "purchase"})
        po = self._make_po(price=800.0)

        action = po.action_create_invoice()
        invoice = self.env["account.move"].browse(action["res_id"])
        invoice.invoice_line_ids.write({"quantity": 1})
        invoice.invoice_line_ids.price_unit = 820.0
        invoice.invoice_date = invoice.date
        invoice.action_post()

        inv_line = invoice.invoice_line_ids
        # A linha da fatura computa o próprio custo líquido (mixin fiscal).
        self.assertAlmostEqual(
            inv_line.stock_cost_unit,
            inv_line.price_unit - inv_line.icms_value,
            places=2,
        )

        picking = po.picking_ids
        self._receive(picking)
        svl = picking.move_ids.stock_valuation_layer_ids
        self.assertAlmostEqual(svl.unit_cost, inv_line.stock_cost_unit, places=2)
        # E não o líquido do pedido:
        self.assertNotEqual(svl.unit_cost, po.order_line.stock_cost_unit)

    def test_invoice_after_receipt_keeps_receipt_cost(self):
        """Fluxo padrão (recebe, fatura depois): o SVL do recebimento usa o
        líquido do pedido e não é retro-alterado pela fatura posterior."""
        po = self._make_po()
        pol = po.order_line
        picking = po.picking_ids
        self._receive(picking)
        svl = picking.move_ids.stock_valuation_layer_ids
        expected = pol.stock_cost_unit
        self.assertAlmostEqual(svl.unit_cost, expected, places=2)

        action = po.action_create_invoice()
        invoice = self.env["account.move"].browse(action["res_id"])
        invoice.invoice_date = invoice.date
        invoice.action_post()
        # SVL do recebimento permanece:
        self.assertAlmostEqual(svl.unit_cost, expected, places=2)

    def test_partial_invoice_before_receipt(self):
        """NF parcial antes do recebimento (5 de 10 faturadas a 820):
        recebimento das 5 faturadas usa o líquido da NF."""
        self.product.write({"purchase_method": "purchase"})
        po = self._make_po(qty=10.0, price=800.0)

        action = po.action_create_invoice()
        invoice = self.env["account.move"].browse(action["res_id"])
        invoice.invoice_line_ids.write({"quantity": 5.0})
        invoice.invoice_line_ids.price_unit = 820.0
        invoice.invoice_date = invoice.date
        invoice.action_post()
        inv_line = invoice.invoice_line_ids

        picking = po.picking_ids
        self._receive(picking, qty_done=5.0)
        done_move = picking.move_ids.filtered(lambda m: m.state == "done")
        svl = done_move.stock_valuation_layer_ids
        self.assertEqual(svl.quantity, 5.0)
        self.assertAlmostEqual(svl.unit_cost, inv_line.stock_cost_unit, places=2)
