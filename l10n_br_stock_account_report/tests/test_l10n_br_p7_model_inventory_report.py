# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class L10nBRP7ModelInventoryReportTest(TransactionCase):
    """Test Brazilian P7 Model Inventory Report"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.p7_report_wizard = cls.env["l10n_br.p7.model.inventory.report.wizard"]

    def test_l10n_br_p7_model_inventory_report(self):
        """Test Brazilian P7 Model Inventory Report."""

        # Create Stock Valuation Layer
        # stock_picking_invoicing.stock_picking_invoicing_7
        picking = self.env.ref("stock_picking_invoicing.stock_picking_invoicing_7")
        # Force product availability
        for move in picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        wizard_obj = self.env["stock.invoice.onshipping"].with_context(
            active_ids=picking.ids,
            active_model=picking._name,
            active_id=picking.id,
            fiscal_operation_journal=False,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()

        wizard_obj = self.p7_report_wizard.with_context(
            default_compute_at_date=0,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard = wizard_obj.create(wizard_values)
        wizard.print_report()
