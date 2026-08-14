# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase
from odoo.tools.float_utils import float_round


class TestStockValuationNetCost(TransactionCase):
    """Incoming stock valued at the net acquisition cost."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company

        # A product of its own: average cost is weighted over existing stock.
        cls.product = cls.env.ref("product.product_product_6").copy(
            {"name": "Net cost product (test)", "is_storable": True}
        )
        cls.supplier_normal = cls.env.ref("l10n_br_base.res_partner_intel")
        cls.supplier_simples = cls.env.ref("l10n_br_base.res_partner_cliente2_sp")
        cls.supplier_normal.tax_framework = "3"
        cls.supplier_simples.tax_framework = "1"

        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.fiscal_operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")

        Account = cls.env["account.account"]
        cls.account_valuation = Account.create(
            {
                "name": "Stock valuation (test)",
                "code": "TSTVAL",
                "account_type": "asset_current",
                "company_ids": [(6, 0, cls.company.ids)],
            }
        )
        cls.account_stock_in = Account.create(
            {
                "name": "Stock input bridge (test)",
                "code": "TSTIN",
                "account_type": "asset_current",
                "company_ids": [(6, 0, cls.company.ids)],
            }
        )
        cls.account_stock_out = Account.create(
            {
                "name": "Stock output bridge (test)",
                "code": "TSTOUT",
                "account_type": "asset_current",
                "company_ids": [(6, 0, cls.company.ids)],
            }
        )
        cls.stock_journal = cls.env["account.journal"].create(
            {
                "name": "Stock journal (test)",
                "code": "TSTJ",
                "type": "general",
                "company_id": cls.company.id,
            }
        )
        cls.categ = cls.product.categ_id
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.valuation_vals = {
            "property_stock_account_input_categ_id": cls.account_stock_in.id,
            "property_stock_account_output_categ_id": cls.account_stock_out.id,
            "property_stock_valuation_account_id": cls.account_valuation.id,
            "property_stock_journal": cls.stock_journal.id,
        }
        cls.categ.with_company(cls.company).write(
            dict(
                cls.valuation_vals,
                property_valuation="real_time",
                property_cost_method="fifo",
            )
        )
        cls.company.stock_valuation_via_stock_price = True

    def _core_price(self, move):
        """The unit price the move is valued at, for a move without lots."""
        return move._get_price_unit()[self.env["stock.lot"]]

    def _set_valuation(self, cost_method, valuation="real_time"):
        self.categ.with_company(self.company).write(
            dict(
                self.valuation_vals,
                property_valuation=valuation,
                property_cost_method=cost_method,
            )
        )

    def _make_incoming(
        self, partner, price_unit=800.0, qty=1.0, fiscal=True, product=None
    ):
        product = product or self.product
        picking_vals = {
            "picking_type_id": self.warehouse.in_type_id.id,
            "location_id": self.env.ref("stock.stock_location_suppliers").id,
            "location_dest_id": self.warehouse.lot_stock_id.id,
            "partner_id": partner.id,
            "company_id": self.company.id,
        }
        move_vals = {
            "name": "purchase test",
            "product_id": product.id,
            "product_uom": product.uom_id.id,
            "product_uom_qty": qty,
            "price_unit": price_unit,
            "company_id": self.company.id,
            "partner_id": partner.id,
        }
        if fiscal:
            picking_vals["fiscal_operation_id"] = self.fiscal_operation.id
            move_vals.update(
                {
                    "fiscal_operation_id": self.fiscal_operation.id,
                    "fiscal_operation_line_id": self.fiscal_operation_line.id,
                }
            )
        picking = self.env["stock.picking"].create(picking_vals)
        move_vals.update(
            {
                "picking_id": picking.id,
                "location_id": picking.location_id.id,
                "location_dest_id": picking.location_dest_id.id,
            }
        )
        # The create of stock.move skips the mapping of the fiscal taxes and
        # hands back the moves under that context: map them as the form does.
        move = (
            self.env["stock.move"]
            .create(move_vals)
            .with_context(skip_compute_fiscal_tax_ids=False)
        )
        move._compute_fiscal_tax_ids()
        return picking, move

    def _receive(self, picking, qty_done=None):
        picking.action_confirm()
        picking.action_assign()
        if qty_done is not None:
            picking.move_ids.move_line_ids.quantity = qty_done
        picking.move_ids.picked = True
        picking.with_context(skip_backorder=True).button_validate()

    # ------------------------------------------------------------------
    # The layer is written from the net cost
    # ------------------------------------------------------------------

    def test_fifo_incoming_net_cost(self):
        """FIFO: the layer holds the net cost, not the gross invoice price."""
        self._set_valuation("fifo")
        picking, move = self._make_incoming(self.supplier_normal)
        self._receive(picking)

        self.assertGreater(move.icms_value, 0, "ICMS should be highlighted")

        svl = move.stock_valuation_layer_ids
        self.assertEqual(len(svl), 1)
        # Presumido industry buying to manufacture: ICMS is credited and so
        # is IPI, while cumulative PIS and COFINS stay in the cost.
        expected = move.price_unit - move.icms_value
        self.assertAlmostEqual(move.cost_unit, expected, places=2)
        self.assertAlmostEqual(svl.unit_cost, move.cost_unit, places=2)
        self.assertNotEqual(svl.unit_cost, move.price_unit)

        account_move = svl.account_move_id
        self.assertTrue(account_move, "real time valuation should post an entry")
        line_val = account_move.line_ids.filtered(
            lambda ln: ln.account_id == self.account_valuation
        )
        line_in = account_move.line_ids.filtered(
            lambda ln: ln.account_id == self.account_stock_in
        )
        self.assertAlmostEqual(line_val.debit, svl.value, places=2)
        self.assertAlmostEqual(line_in.credit, svl.value, places=2)

    def test_manual_creditability_survives_validation(self):
        """A decision taken by the user is not derived again on validation."""
        reason = self.env["l10n_br_fiscal.creditability.reason"].create(
            {
                "code": "TEST-VALIDATION",
                "name": "Benefit conditioned on waiving the credit",
                "kind": "benefit",
                "legal_basis": "Decreto estadual de exemplo, art. 1",
            }
        )
        self._set_valuation("fifo")
        picking, move = self._make_incoming(self.supplier_normal)
        move.write(
            {
                "creditability_origin": "manual",
                "creditability_reason_id": reason.id,
                "icms_tax_is_creditable": False,
            }
        )
        self._receive(picking)

        self.assertAlmostEqual(
            move.stock_valuation_layer_ids.unit_cost, move.price_unit, places=2
        )

    def test_avco_incoming_net_cost(self):
        """AVCO: the average cost of the product becomes the net one."""
        self._set_valuation("average")
        self.assertFalse(self.product.quantity_svl)

        picking, move = self._make_incoming(self.supplier_normal)
        self._receive(picking)

        svl = move.stock_valuation_layer_ids
        self.assertAlmostEqual(svl.unit_cost, move.cost_unit, places=2)
        self.assertAlmostEqual(
            self.product.with_company(self.company).standard_price,
            move.cost_unit,
            places=2,
        )

    # ------------------------------------------------------------------
    # Where the net cost does not reach
    # ------------------------------------------------------------------

    def test_net_cost_keeps_product_price_precision(self):
        """The net cost and its layer keep the Product Price decimals.

        A Monetary field would round both to the currency decimals on write.
        """
        self.env.ref("product.decimal_price").digits = 4
        self._set_valuation("fifo")
        picking, move = self._make_incoming(
            self.supplier_normal, price_unit=100.01, qty=7.0
        )
        self._receive(picking)
        svl = move.stock_valuation_layer_ids
        move.invalidate_recordset(["cost_unit"])
        svl.invalidate_recordset(["unit_cost"])

        # Without a third or fourth decimal the test would prove nothing.
        self.assertNotEqual(
            float_round(move.cost_unit, precision_digits=2), move.cost_unit
        )
        self.assertEqual(
            float_round(move.cost_unit, precision_digits=4), move.cost_unit
        )
        self.assertAlmostEqual(svl.unit_cost, move.cost_unit, places=4)

    def test_standard_cost_ignores_net_cost(self):
        """Standard costing prices the layer from the product, not the move."""
        self._set_valuation("standard")
        self.product.with_company(self.company).standard_price = 500.0
        picking, move = self._make_incoming(self.supplier_normal)
        self._receive(picking)

        svl = move.stock_valuation_layer_ids
        self.assertAlmostEqual(svl.unit_cost, 500.0, places=2)
        self.assertNotAlmostEqual(svl.unit_cost, move.cost_unit, places=2)

    def test_periodic_inventory_keeps_gross_cost(self):
        """Under periodic inventory the net cost abstains."""
        self._set_valuation("fifo", valuation="manual_periodic")
        picking, move = self._make_incoming(self.supplier_normal)
        self._receive(picking)

        svl = move.stock_valuation_layer_ids
        self.assertTrue(svl)
        self.assertFalse(svl.account_move_id)
        self.assertAlmostEqual(svl.unit_cost, move.price_unit, places=2)

    # ------------------------------------------------------------------
    # Supplier regime
    # ------------------------------------------------------------------

    def test_supplier_simples_valuation(self):
        """A Simples supplier highlights no ICMS, so none is credited."""
        self._set_valuation("fifo")
        picking, move = self._make_incoming(self.supplier_simples)
        self._receive(picking)

        svl = move.stock_valuation_layer_ids
        self.assertFalse(move.icms_tax_is_creditable)
        self.assertGreater(move.icms_value, 0)

        expected = move.fiscal_amount_total - move.ipi_value
        self.assertAlmostEqual(move.cost_unit, expected, places=2)
        self.assertAlmostEqual(svl.unit_cost, move.cost_unit, places=2)
        # The embedded ICMS was kept, so the cost is not reduced by it.
        self.assertAlmostEqual(svl.unit_cost, move.price_unit, places=2)

    # ------------------------------------------------------------------
    # Partial receipt, invoice price and the non Brazilian path
    # ------------------------------------------------------------------

    def test_partial_receipt_net_cost(self):
        """Receiving 3 of 10 values those 3 at the unit net cost."""
        self._set_valuation("fifo")
        picking, move = self._make_incoming(self.supplier_normal, qty=10.0)
        self._receive(picking, qty_done=3.0)

        done_move = picking.move_ids.filtered(lambda m: m.state == "done")
        svl = done_move.stock_valuation_layer_ids
        self.assertEqual(svl.quantity, 3.0)

        expected_unit = done_move.price_unit - (
            done_move.icms_value / done_move.product_uom_qty
        )
        self.assertAlmostEqual(done_move.cost_unit, expected_unit, places=2)
        self.assertAlmostEqual(svl.value, 3.0 * expected_unit, places=2)

    def test_invoice_price_unaffected(self):
        """The invoice keeps the invoice price, never the net cost."""
        self._set_valuation("fifo")
        picking, move = self._make_incoming(self.supplier_normal)
        self._receive(picking)

        invoice_price = move._get_price_unit_invoice("in_invoice", move.partner_id)
        self.assertAlmostEqual(invoice_price, move.price_unit, places=2)
        self.assertNotEqual(invoice_price, move.cost_unit)

    def test_no_fiscal_operation_core_behavior(self):
        """Without a fiscal operation the core behaviour is untouched."""
        self._set_valuation("fifo")
        picking, move = self._make_incoming(self.supplier_normal, fiscal=False)
        self._receive(picking)

        svl = move.stock_valuation_layer_ids
        self.assertAlmostEqual(svl.unit_cost, move.price_unit, places=2)

    def test_missing_operation_line_keeps_core_price(self):
        """A move with no operation line computes no cost and keeps the core price."""
        self._set_valuation("fifo")
        picking, move = self._make_incoming(self.supplier_normal)
        move.fiscal_operation_line_id = False

        self.assertFalse(move.cost_unit)
        self.assertAlmostEqual(self._core_price(move), move.price_unit, places=2)

        self._receive(picking)
        svl = move.stock_valuation_layer_ids
        self.assertAlmostEqual(svl.unit_cost, move.price_unit, places=2)
        self.assertGreater(svl.value, 0)
