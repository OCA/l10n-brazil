# -*- coding: utf-8 -*-
# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo.tests.common as common


class TestL10nBRSaleStock(common.TransactionCase):

    def setUp(self):
        super(TestL10nBRSaleStock, self).setUp()
        self.sale_object = self.env['sale.order']
        self.sale_stock = self.sale_object.browse(
            self.ref('l10n_br_sale_stock.l10n_br_sale_stock_demo_1')
        )
        self.stock_invoice_onshipping = self.env['stock.invoice.onshipping']
        self.invoice_model = self.env['account.invoice']

    def test_create_invoice_with_field_inconterm(self):
        """ Test create invoice with field inconterm."""

        self.sale_stock.onchange_partner_id()
        self.sale_stock.onchange_partner_shipping_id()

        for line in self.sale_stock.order_line:
            line.product_id_change()
            line.onchange_fiscal()

        self.sale_stock.action_confirm()

        # Create and check invoice
        self.sale_stock.action_invoice_create(final=True)

        for invoice in self.sale_stock.invoice_ids:
            self.assertTrue(
                invoice.incoterms_id,
                "Error to included Inconterms on invoice"
                " dictionary from Sale Order."
            )

    def test_l10n_br_sale_stock(self):
        """Test creation of invoice from picking generate by Sale Order"""

        self.sale_stock.onchange_partner_id()
        self.sale_stock.onchange_partner_shipping_id()
        for line in self.sale_stock.order_line:
            line.product_id_change()
            line.onchange_fiscal()
            self.assertTrue(
                line.fiscal_position_id,
                "Error to mapping Fiscal Position on Sale Order Line."
            )

        self.sale_stock.action_confirm()
        self.assertTrue(
            self.sale_stock.picking_ids,
            'Sale Stock: no picking created for'
            ' "invoice on delivery" stockable products')

        pick = self.sale_stock.picking_ids
        for line in pick.move_lines:
            self.assertTrue(
                line.fiscal_position_id,
                "Error to mapping Fiscal Position on Move Line."
            )

        # We need to inform this picking To be Invoiced
        pick.set_to_be_invoiced()

        pick.action_confirm()
        pick.force_assign()
        pick.do_new_transfer()
        pick.action_done()

        wizard_obj = self.stock_invoice_onshipping.with_context(
            active_ids=[pick.id],
            active_model=pick._name,
            active_id=pick.id,
        ).create({
            'group': 'picking',
            'journal_type': 'sale'
        })
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        action = wizard.action_generate()
        domain = action.get('domain', [])
        invoice = self.invoice_model.search(domain)

        self.assertTrue(invoice, 'Invoice is not created.')
        for line in invoice.picking_ids:
            self.assertEquals(
                line.id, pick.id,
                'Relation between invoice and picking are missing.')
        for line in invoice.invoice_line_ids:
            self.assertTrue(
                line.invoice_line_tax_ids,
                'Taxes in invoice lines are missing.'
            )
        self.assertTrue(
            invoice.tax_line_ids, 'Total of Taxes in Invoice are missing.'
        )
        self.assertTrue(
            invoice.fiscal_position_id,
            'Mapping fiscal position on wizard to create invoice fail.'
        )
