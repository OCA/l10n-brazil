# -*- coding: utf-8 -*-
# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo.tests.common as common


class TestL10nBRSale(common.TransactionCase):

    def setUp(self):
        super(TestL10nBRSale, self).setUp()
        self.sale_object = self.env['sale.order']
        self.sale_order_1 = self.sale_object.browse(
            self.ref('l10n_br_sale.sale_order_teste_1')
        )
        self.fiscal_categ_venda = self.env[
            'l10n_br_account.fiscal.category'].browse(
            self.ref(
                'l10n_br_sale.demo_fiscal_category-venda'))
        self.fiscal_categ_venda_st = self.env[
            'l10n_br_account.fiscal.category'].browse(
            self.ref(
                'l10n_br_sale.demo_fiscal_category-venda_sp_st'))

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
            line.fiscal_category_id = self.fiscal_categ_venda_st.id
            line.product_id_change()
            line.onchange_fiscal()
            self.assertTrue(
                line.fiscal_position_id,
                "Error to mapping Fiscal Position on Sale Order Line."
            )
            for tax in line.tax_id:
                self.assertEquals(
                    tax.name, u'IPI Saída 5% - l10n_br_sale',
                    u"Error to mapping correct TAX ( IPI Saída 5%"
                    u" - l10n_br_sale)."
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
                line.fiscal_position_id.name, 'Venda para Dentro do Estado',
                "Error to mapping correct Fiscal Position on Sale Order Line"
                " after change fiscal category."
            )
            for tax in line.tax_id:
                if tax.tax_group_id.name == 'IPI':
                    self.assertEquals(
                        tax.name, u'IPI Saída 2% - l10n_br_sale',
                        u"Error to mapping correct TAX ("
                        u" IPI Saída 2% - l10n_br_sale)."
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
            for line in invoice.invoice_line_ids:
                self.assertTrue(
                    line.fiscal_position_id,
                    "Error to mapping Fiscal Position on Sale Order Line."
                )
                for tax in line.invoice_line_tax_ids:
                    if tax.tax_group_id.name == 'IPI':
                        self.assertEquals(
                            tax.name, u'IPI Saída 2% - l10n_br_sale',
                            u"Error to mapping correct TAX ("
                            u" IPI Saída 2% - l10n_br_sale)."
                        )

    def test_l10n_br_sale_discount(self):
        self.sale_discount = self.sale_object.create(dict(
            name='TESTE DESCONTO',
            partner_id=self.env.ref(
                'l10n_br_base.res_partner_akretion').id,
            partner_invoice_id=self.env.ref(
                'l10n_br_base.res_partner_akretion').id,
            partner_shipping_id=self.env.ref(
                'l10n_br_base.res_partner_akretion').id,
            user_id=self.env.ref('base.user_demo').id,
            pricelist_id=self.env.ref('product.list0').id,
            team_id=self.env.ref('sales_team.crm_team_1').id,
            state='draft',
            fiscal_category_id=self.env.ref(
                'l10n_br_account_product.'
                'fc_78df616ab31e95ee46c6a519a2ce9e12').id,
            order_line=[(0, 0, dict(
                name='TESTE DISCOUNT',
                product_id=self.env.ref('product.product_product_27').id,
                product_uom_qty=1,
                product_uom=self.env.ref('product.product_uom_unit').id,
                price_unit=100,
                fiscal_category_id=self.env.ref(
                    'l10n_br_account_product.'
                    'fc_78df616ab31e95ee46c6a519a2ce9e12').id
            ))]
        ))
        self.sale_discount.onchange_partner_id()
        self.sale_discount.onchange_partner_shipping_id()
        self.sale_discount.discount_rate = 10.0
        self.sale_discount.onchange_discount_rate()
        # Test Discount
        self.assertEquals(
            self.sale_discount.amount_total, 90.0,
            u"Error to apply discount on sale order."
        )
        self.sale_discount.action_confirm()
        # Create and check invoice
        self.sale_discount.action_invoice_create(final=True)
        for invoice in self.sale_discount.invoice_ids:
            self.assertEquals(
                invoice.amount_untaxed, 90.0,
                u"Error to apply discount on invoice"
                u" created from sale order."
            )
