# -*- coding: utf-8 -*-
# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class ProcurementOrderTest(TransactionCase):
    """Test invoicing picking"""

    def setUp(self):
        super(ProcurementOrderTest, self).setUp()
        self.product_1 = self.env.ref('stock.product_icecream')
        self.uom_unit = self.env.ref('product.product_uom_unit')
        # Warehouses
        self.warehouse_1 = self.env['stock.warehouse'].create({
            'name': 'Base Warehouse',
            'reception_steps': 'one_step',
            'delivery_steps': 'ship_only',
            'code': 'BWH'})
        # Locations
        self.location_1 = self.env['stock.location'].create({
            'name': 'TestLocation1',
            'posx': 3,
            'location_id': self.warehouse_1.lot_stock_id.id,
        })
        self.warehouse_2 = self.env['stock.warehouse'].create({
            'name': 'Small Warehouse',
            'code': 'SWH',
            'default_resupply_wh_id': self.warehouse_1.id,
            'resupply_wh_ids': [(6, 0, [self.warehouse_1.id])]
        })

        # minimum stock rule for test product on this warehouse
        self.env['stock.warehouse.orderpoint'].create({
            'warehouse_id': self.warehouse_2.id,
            'location_id': self.warehouse_2.lot_stock_id.id,
            'product_id': self.product_1.id,
            'product_min_qty': 10,
            'product_max_qty': 100,
            'product_uom': self.uom_unit.id,
        })

    def test_procument_order(self):
        """Test Procurement Order"""

        # Inform Partner and Fiscal Category in Procurement Rule just
        # for test
        self.procurement_rule = self.env['procurement.rule'].search([(
            'name', '=', 'SWH: YourCompany: Transit Location -> Stock'
        )])
        self.procurement_rule.partner_address_id = self.env.ref(
            'l10n_br_base.res_partner_amd').id
        self.procurement_rule.fiscal_category_id = self.env.ref(
            'l10n_br_account_product.fc_86d8c770fc2fb9d9fa242a3bdddd507a').id

        OrderScheduler = self.env['procurement.order']
        OrderScheduler.run_scheduler()
        # we generated 2 procurements for product A:
        # one on small wh and the other one on the transit location
        procs = OrderScheduler.search([('product_id', '=', self.product_1.id)])
        self.assertEqual(len(procs), 2)

        proc1 = procs.filtered(
            lambda order: order.warehouse_id == self.warehouse_2)
        self.assertEqual(proc1.state, 'running')

        proc2 = procs.filtered(
            lambda order: order.warehouse_id == self.warehouse_1)
        self.assertEqual(proc2.location_id.usage, 'transit')
        self.assertNotEqual(proc2.state, 'exception')

        proc2.run()
        self.assertEqual(proc2.state, 'running')
        self.assertTrue(proc2.rule_id)
