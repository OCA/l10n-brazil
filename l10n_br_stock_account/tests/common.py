# Copyright (C) 2023-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form, TransactionCase


class TestBrPickingInvoicingCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def _change_user_company(self, company):
        self.env.user.company_ids += company
        self.env.user.company_id = company

    def _run_fiscal_onchanges(self, record):
        record._onchange_fiscal_operation_id()

    def _run_fiscal_line_onchanges(self, record):
        # Mixin Fiscal
        record._onchange_commercial_quantity()

        # Stock Move
        record._onchange_product_id_fiscal()
        record._onchange_fiscal_taxes()
        record._onchange_product_quantity()

    def picking_move_state(self, picking):
        self._run_fiscal_onchanges(picking)
        picking.action_confirm()
        # Check product availability
        picking.action_assign()
        # Force product availability
        for move in picking.move_ids_without_package:
            self._run_fiscal_line_onchanges(move)
            move.quantity_done = move.product_uom_qty
        picking.button_validate()

    def create_invoice_wizard(self, pickings):
        wizard_obj = self.env["stock.invoice.onshipping"].with_context(
            active_ids=pickings.ids,
            active_model=pickings._name,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        # One invoice per partner but group products
        wizard_values.update({"group": "partner_product"})
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()
        domain = [("picking_ids", "in", pickings.ids)]
        invoice = self.env["account.move"].search(domain)
        return invoice

    def return_picking_wizard(self, picking):
        # Return Picking
        return_wizard_form = Form(
            self.env["stock.return.picking"].with_context(
                **dict(active_id=picking.id, active_model="stock.picking")
            )
        )
        return_wizard_form.invoice_state = "2binvoiced"
        self.return_wizard = return_wizard_form.save()

        result_wizard = self.return_wizard.create_returns()
        self.assertTrue(result_wizard, "Create returns wizard fail.")
        picking_devolution = self.env["stock.picking"].browse(
            result_wizard.get("res_id")
        )
        return picking_devolution

    def create_backorder_wizard(self, picking):
        res_dict_for_back_order = picking.button_validate()
        backorder_wizard = Form(
            self.env[res_dict_for_back_order["res_model"]].with_context(
                **res_dict_for_back_order["context"]
            )
        ).save()
        backorder_wizard.process()
        backorder = self.env["stock.picking"].search(
            [("backorder_id", "=", picking.id)]
        )
        return backorder
