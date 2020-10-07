# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class InvoicingPickingTest(TransactionCase):
    """Test invoicing picking"""

    def setUp(self):
        super(InvoicingPickingTest, self).setUp()
        # self.env = self.env(user=self.env.ref('l10n_br_base.user_demo_presumido'))
        self.stock_picking = self.env['stock.picking']
        self.invoice_model = self.env['account.invoice']
        self.stock_invoice_onshipping = self.env['stock.invoice.onshipping']
        self.stock_return_picking = self.env['stock.return.picking']
        self.stock_picking_sp = self.env.ref(
            'l10n_br_stock_account.demo_l10n_br_stock_account-picking-1')

    def _run_fiscal_onchanges(self, record):
        record._onchange_fiscal_operation_id()

    def _run_fiscal_line_onchanges(self, record):
        record._onchange_product_id_fiscal()
        record._onchange_fiscal_operation_id()
        record._onchange_fiscal_operation_line_id()
        record._onchange_fiscal_taxes()

    def test_invoicing_picking(self):
        """Test Invoicing Picking"""

        self._run_fiscal_onchanges(self.stock_picking_sp)

        for line in self.stock_picking_sp.move_lines:
            self._run_fiscal_line_onchanges(line)

        self.stock_picking_sp.action_confirm()
        self.stock_picking_sp.action_assign()

        # Force product availability
        for move in self.stock_picking_sp.move_ids_without_package:
            move.quantity_done = move.product_uom_qty

        self.stock_picking_sp.button_validate()

        self.assertEquals(
            self.stock_picking_sp.state, 'done',
            'Change state fail.'
        )

        wizard_obj = self.stock_invoice_onshipping.with_context(
            active_ids=[self.stock_picking_sp.id],
            active_model=self.stock_picking_sp._name,
            active_id=self.stock_picking_sp.id,
        ).create({
            'group': 'picking',
            'journal_type': 'sale'
        })

        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()
        domain = [('picking_ids', '=', self.stock_picking_sp.id)]
        invoice = self.invoice_model.search(domain)

        self.assertTrue(invoice, 'Invoice is not created.')
        for line in invoice.picking_ids:
            self.assertEquals(
                line.id, self.stock_picking_sp.id,
                'Relation between invoice and picking are missing.')
        for line in invoice.invoice_line_ids:
            self.assertTrue(
                line.invoice_line_tax_ids,
                'Taxes in invoice lines are missing.'
            )
        # tax_line_ids is not created if all the taxes have value 0
        # self.assertTrue(
        #     invoice.tax_line_ids, 'Total of Taxes in Invoice are missing.'
        # )
        self.assertTrue(
            invoice.fiscal_operation_id,
            'Mapping fiscal operation on wizard to create invoice fail.'
        )
        self.assertTrue(
            invoice.fiscal_document_id,
            'Mapping Fiscal Documentation_id on wizard to create invoice fail.'
        )

        self.return_wizard = self.stock_return_picking.with_context(
            dict(active_id=self.stock_picking_sp.id)).create(
            dict(invoice_state='2binvoiced'))
        for line in self.return_wizard.product_return_moves:
            line.quantity = line.move_id.product_uom_qty

        result = self.return_wizard.create_returns()
        self.assertTrue(result, 'Create returns wizard fail.')

    def test_invoicing_picking_overprocessed(self):
        """Test Invoicing Picking overprocessed EXTRA Fields"""

        self._run_fiscal_onchanges(self.stock_picking_sp)

        for line in self.stock_picking_sp.move_lines:
            self._run_fiscal_line_onchanges(line)

        self.stock_picking_sp.action_confirm()
        self.stock_picking_sp.action_assign()

        # Force product availability
        for move in self.stock_picking_sp.move_ids_without_package:
            # Overprocessed
            move.quantity_done = move.product_uom_qty + 1

        res_overprocessed_transfer = self.stock_picking_sp.button_validate()
        stock_overprocessed_transfer = self.env[
            'stock.overprocessed.transfer'].browse(
            res_overprocessed_transfer.get('res_id'))
        stock_overprocessed_transfer.action_confirm()

        self.assertEquals(
            self.stock_picking_sp.state, 'done',
            'Change state fail.'
        )
