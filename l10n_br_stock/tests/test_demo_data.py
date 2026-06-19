# Copyright (C) 2026  Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDemoDataHooks(TransactionCase):
    """Test that the hooks in l10n_br_stock correctly set up demo data.

    These hooks run during module installation (pre_init_hook and
    post_init_hook). They create demo warehouses, set external IDs on
    warehouse sub-records (locations, picking types), and create stock
    quants so that other modules (sale_stock, purchase_stock, ...) have
    inventory to work with.
    """

    # ---- warehouse external ID suffixes set by set_stock_warehouse_external_ids
    WH_XID_SUFFIXES = [
        "",
        "_loc_stock_id",
        "_view_location",
        "_input_location",
        "_quality_control_location",
        "_pack_location",
        "_output_location",
        "_picking_type_in",
        "_picking_type_internal",
        "_pick_type_internal",
        "_pack_type_internal",
        "_picking_type_out",
    ]

    def _resolve_warehouse(self, company_xid):
        """Resolve a warehouse via its external ID and assert it exists."""
        wh = self.env.ref(company_xid, raise_if_not_found=False)
        self.assertTrue(wh, f"Warehouse {company_xid} should exist")
        return wh

    def test_warehouse_external_ids(self):
        """Warehouses for demo companies have proper external IDs."""
        for company_xid in (
            "l10n_br_stock.wh_empresa_simples_nacional",
            "l10n_br_stock.wh_empresa_lucro_presumido",
        ):
            wh = self._resolve_warehouse(company_xid)
            self.assertTrue(wh.active, f"Warehouse {company_xid} should be active")
            self.assertTrue(
                wh.lot_stock_id, f"{company_xid} should have a stock location"
            )

    def test_warehouse_sub_records_external_ids(self):
        """All warehouse sub-records (locations, picking types) have xids."""
        for prefix in (
            "l10n_br_stock.wh_empresa_simples_nacional",
            "l10n_br_stock.wh_empresa_lucro_presumido",
        ):
            for suffix in self.WH_XID_SUFFIXES:
                xid = f"{prefix}{suffix}"
                record = self.env.ref(xid, raise_if_not_found=False)
                self.assertTrue(
                    record,
                    f"External ID {xid} should resolve to a record",
                )

    def test_warehouse_company_link(self):
        """Each warehouse is linked to the correct demo company."""
        company_sn = self.env.ref("l10n_br_base.empresa_simples_nacional")
        company_lp = self.env.ref("l10n_br_base.empresa_lucro_presumido")
        wh_sn = self._resolve_warehouse("l10n_br_stock.wh_empresa_simples_nacional")
        wh_lp = self._resolve_warehouse("l10n_br_stock.wh_empresa_lucro_presumido")
        self.assertEqual(wh_sn.company_id, company_sn)
        self.assertEqual(wh_lp.company_id, company_lp)

    def test_stock_quants_created(self):
        """post_init_hook created quants with inventory for demo products."""
        wh_sn = self._resolve_warehouse("l10n_br_stock.wh_empresa_simples_nacional")
        quants = self.env["stock.quant"].search(
            [("location_id", "=", wh_sn.lot_stock_id.id)]
        )
        self.assertTrue(
            quants,
            "Should have stock quants in Simples Nacional warehouse",
        )
        # The hook creates 500 units per product; at least some should remain
        product_24 = self.env.ref("product.product_product_24")
        quant_24 = quants.filtered(lambda q: q.product_id == product_24)
        self.assertTrue(
            quant_24,
            "product_product_24 should have a quant in the ESN warehouse",
        )

    def test_demo_shelf_locations(self):
        """Demo shelf locations are correctly linked to warehouse stock."""
        loc_sn = self.env.ref("l10n_br_stock.wh_empresa_simples_nacional_loc_stock_id")
        loc_lp = self.env.ref("l10n_br_stock.wh_empresa_lucro_presumido_loc_stock_id")
        shelf_sn_1 = self.env.ref("l10n_br_stock.stock_location_sn_shelf_1")
        shelf_lp_1 = self.env.ref("l10n_br_stock.stock_location_lp_shelf_1")
        self.assertEqual(shelf_sn_1.location_id, loc_sn)
        self.assertEqual(shelf_lp_1.location_id, loc_lp)

    def test_picking_search_by_partner_fields(self):
        """Stock picking search view supports legal_name and IE search."""
        # The model has the related fields
        picking = self.env["stock.picking"].new()
        self.assertIn(
            "legal_name",
            picking._fields,
            "stock.picking should have legal_name field",
        )
        self.assertIn(
            "l10n_br_ie_code",
            picking._fields,
            "stock.picking should have l10n_br_ie_code field",
        )

        # The fields are searchable (have a search method or are stored)
        partner = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        if partner.legal_name or partner.name:
            pickings = self.env["stock.picking"].search(
                [("legal_name", "ilike", partner.name or "")]
            )
            # search should not raise even if no results
            self.assertIsInstance(pickings, type(self.env["stock.picking"]))
