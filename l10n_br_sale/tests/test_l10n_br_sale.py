# -*- coding: utf-8 -*-
# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo.tests.common as common


class TestL10nBRSale(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.sale_object = self.env['sale.order']
        self.sale_order_1 = self.sale_object.browse(
            self.ref('l10n_br_sale.sale_order_teste_1')
        )
        self.fiscal_categ_venda = self.env[
            'l10n_br_account.fiscal.category'].browse(
            self.ref('l10n_br_sale.fiscal_category_venda'))
        self.fiscal_categ_venda_st = self.env[
            'l10n_br_account.fiscal.category'].browse(
            self.ref('l10n_br_sale.fiscal_category_venda_st'))

    def test_l10n_br_sale_order(self):
        self.sale_order_1.onchange_partner_id()
        self.sale_order_1.onchange_partner_shipping_id()
        self.assertTrue(
            self.sale_order_1.fiscal_position_id,
            "Error to mapping Fiscal Position on Sale Order."
        )
        # Change Fiscal Category to test mapping Fiscal Position
        self.sale_order_1.fiscal_category_id = self.fiscal_categ_venda_st.id
        self.sale_order_1.onchange_partner_id()
        self.sale_order_1.onchange_partner_shipping_id()
        self.assertTrue(
            self.sale_order_1.fiscal_position_id,
            "Error to mapping Fiscal Position on Sale Order"
            "after change fiscal category."
        )
        self.assertEquals(
            self.sale_order_1.fiscal_position_id.name, 'Venda SP c/ ST',
            "Error to mapping correct Fiscal Position on Sale Order"
            "after change fiscal category."
        )
        for line in self.sale_order_1.order_line:
            line.product_id_change()
            line.onchange_fiscal()
            self.assertTrue(
                line.fiscal_position_id,
                "Error to mapping Fiscal Position on Sale Order Line."
            )
            for tax in line.tax_id:
                self.assertEquals(
                    tax.name, u'IPI Saída 3%',
                    u"Error to mapping correct TAX ( IPI Saída 3% )."
                )
            # Change Fiscal Category
            line.fiscal_category_id = self.fiscal_categ_venda.id
            line.onchange_fiscal()
            self.assertTrue(
                line.fiscal_position_id,
                "Error to mapping Fiscal Position on Sale Order Line"
                "after change fiscal category."
            )
            self.assertEquals(
                line.fiscal_position_id.name, 'Venda SP',
                "Error to mapping correct Fiscal Position on Sale Order Line"
                "after change fiscal category."
            )
            for tax in line.tax_id:
                self.assertEquals(
                    tax.name, u'IPI Saída 2%',
                    u"Error to mapping correct TAX ( IPI Saída 2% )."
                )
        self.sale_order_1.action_confirm()

        # Create and check invoice
        self.sale_order_1.action_invoice_create(final=True)
        self.assertEquals(
            self.sale_order_1.state, 'sale',
            "Error to confirm Sale Order."
        )
        for invoice in self.sale_order_1.invoice_ids:
            self.assertTrue(
                invoice.fiscal_category_id,
                "Error to included Fiscal Category on invoice"
                " dictionary from Sale Order."
            )
            self.assertTrue(
                invoice.fiscal_position_id,
                "Error to included Fiscal Position on invoice"
                " dictionary from Sale Order."
            )
