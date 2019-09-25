# -*- coding: utf-8 -*-
# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo.tests.common as common


class TestL10nBRPurchase(common.TransactionCase):

    def setUp(self):
        super(TestL10nBRPurchase, self).setUp()
        self.purchase_object = self.env['purchase.order']
        self.purchase_order_1 = self.purchase_object.browse(
            self.ref('l10n_br_purchase.l10n_br_purchase_order-demo_1')
        )
        self.fiscal_categ_compras = self.env[
            'l10n_br_account.fiscal.category'].browse(
            self.ref(
                'l10n_br_purchase.demo_fiscal_category-compras'))
        self.fiscal_categ_compras_st = self.env[
            'l10n_br_account.fiscal.category'].browse(
            self.ref(
                'l10n_br_purchase.demo_fiscal_category-compras_sp_st'))
        self.stock_invoice_onshipping = self.env['stock.invoice.onshipping']
        self.invoice_model = self.env['account.invoice']

    def test_l10n_br_purchase_order(self):
        """
        Test Purchase Order mapping Fiscal Position, Taxes
        and create Invoice based on Picking.
        """

        self.purchase_order_1.onchange_partner_id()
        self.purchase_order_1.onchange_fiscal()
        self.assertTrue(
            self.purchase_order_1.fiscal_position_id,
            "Error to mapping Fiscal Position on Sale Order."
        )
        # Change Fiscal Category to test mapping Fiscal Position
        self.purchase_order_1.fiscal_category_id = \
            self.fiscal_categ_compras_st.id
        self.purchase_order_1.onchange_partner_id()
        self.purchase_order_1.onchange_fiscal()
        self.assertTrue(
            self.purchase_order_1.fiscal_position_id,
            "Error to mapping Fiscal Position on Sale Order"
            "after change fiscal category."
        )
        self.assertEquals(
            self.purchase_order_1.fiscal_position_id.name, 'Compra SP c/ ST',
            "Error to mapping correct Fiscal Position on Sale Order"
            "after change fiscal category."
        )
        for line in self.purchase_order_1.order_line:
            line.fiscal_category_id = self.fiscal_categ_compras_st.id
            line.onchange_product_id()
            line.onchange_fiscal()
            self.assertTrue(
                line.fiscal_position_id,
                "Error to mapping Fiscal Position on Sale Order Line."
            )

            for tax in line.taxes_id:
                if tax.tax_group_id.name == 'IPI':
                    self.assertEquals(
                        tax.name, u'IPI Entrada 10% *',
                        u"Error to mapping correct TAX (IPI Entrada 15% *)"
                    )

            # Change Fiscal Category
            line.fiscal_category_id = self.fiscal_categ_compras.id
            line.onchange_fiscal()
            self.assertTrue(
                line.fiscal_position_id,
                "Error to mapping Fiscal Position on Purchase Order Line"
                "after change fiscal category."
            )
            self.assertEquals(
                line.fiscal_position_id.name,
                'Compra para Dentro do Estado',
                "Error to mapping correct Fiscal Position on"
                " Purchase Order Line after change fiscal category."
            )
            for tax in line.taxes_id:
                if tax.tax_group_id.name == 'IPI':
                    self.assertEquals(
                        tax.name, u'IPI Entrada 2% *',
                        u"Error to mapping correct TAX ("
                        u" IPI Entrada 2% *)."
                    )
        self.purchase_order_1.button_confirm()

        self.assertEquals(
            self.purchase_order_1.state, 'purchase',
            "Error to confirm Purchase Order."
        )

        self.assertTrue(
            self.purchase_order_1.picking_ids,
            'Purchase Order: no picking created for'
            ' "invoice on delivery" stockable products')

        pick = self.purchase_order_1.picking_ids
        for line in pick.move_lines:
            self.assertTrue(
                line.fiscal_category_id,
                "Error to mapping Fiscal Category on Move Line."
            )
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
        self.assertEquals(
            self.purchase_order_1.invoice_status, 'to invoice',
            "Error in compute field invoice_status,"
            " before create invoice by Picking."
        )

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

        self.assertTrue(
            invoice.purchase_id,
            'Relation purchase_id in invoice are missing.')
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
                line.purchase_line_id,
                'Relation purchase_line_id in invoice lines are missing.'
            )
            for tax in line.invoice_line_tax_ids:
                if tax.tax_group_id.name == 'IPI':
                    self.assertEquals(
                        tax.name, u'IPI Entrada 2% *',
                        u"Error to mapping correct TAX ("
                        u" IPI Entrada 2% *)."
                    )
        self.assertTrue(
            invoice.tax_line_ids, 'Total of Taxes in Invoice are missing.'
        )
        self.assertTrue(
            invoice.fiscal_position_id,
            'Mapping fiscal position on wizard to create invoice fail.'
        )
        self.assertEquals(
            self.purchase_order_1.invoice_status, 'invoiced',
            'Error in compute field invoice_status,'
            ' after create Invoice from Picking.'
        )
