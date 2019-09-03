# -*- coding: utf-8 -*-
# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo.tests.common as common


class TestL10nBRSaleProduct(common.TransactionCase):

    def setUp(self):
        super(TestL10nBRSaleProduct, self).setUp()
        self.sale_object = self.env['sale.order']
        self.sale_stock = self.sale_object.browse(
            self.ref('l10n_br_sale_product.l10n_br_sale_product_demo_1')
        )

    def test_l10n_br_sale_product(self):
        """Test fields implemented by l10n_br_sale_product"""

        self.sale_stock.onchange_partner_id()
        self.sale_stock.onchange_partner_shipping_id()
        for line in self.sale_stock.order_line:
            line.product_id_change()
            line.onchange_fiscal()
            self.assertTrue(
                line.fiscal_position_id,
                "Error to mapping Fiscal Position on Sale Order Line."
            )

        self.assertEquals(
            self.sale_stock.amount_total, 7473.3,
            u"Error to apply discount on sale order."
        )
        self.assertEquals(
            self.sale_stock.amount_freight, 6.0,
            u"Error to calculate Total Amount Freight."
        )
        self.assertEquals(
            self.sale_stock.amount_costs, 2.0,
            u"Error to calculate Total Amount Costs."
        )
        self.assertEquals(
            self.sale_stock.amount_extra, 12.0,
            u"Error to calculate Total Amount Extra"
        )
        self.assertEquals(
            self.sale_stock.amount_insurance, 4.0,
            u"Error to calculate Total Amount Extra"
        )
        self.sale_stock.action_confirm()
        # Create and check invoice
        self.sale_stock.action_invoice_create(final=True)
        for invoice in self.sale_stock.invoice_ids:
            self.assertEquals(
                invoice.amount_untaxed, 7315.0,
                u"Error to apply discount on invoice"
                u" created from sale order."
            )
            for line in invoice.invoice_line_ids:
                self.assertTrue(
                    line.company_id,
                    "Error to inform field company_id on Sale Order Line."
                )
                self.assertTrue(
                    line.partner_id,
                    "Error to inform field partner_id on Sale Order Line."
                )
