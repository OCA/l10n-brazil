# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo.tests.common as common


class TestL10nBRSale(common.TransactionCase):
    def setUp(self):
        super(TestL10nBRSale, self).setUp()
        self.sale_object = self.env["sale.order"]
        self.sale_order_1 = self.sale_object.browse(
            self.ref("l10n_br_sale.sale_order_teste_1")
        )
        self.operation_line_revenda = self.env[
            'l10n_br_fiscal.document.line'].browse(
            self.ref('l10n_br_fiscal.fo_venda_revenda'))

    def test_l10n_br_sale_order(self):
        """ Test brazilian fiscal mapping. """
        self.sale_order_1.onchange_partner_id()
        self.sale_order_1.onchange_partner_shipping_id()
        self.assertTrue(
            self.sale_order_1.operation_id,
            "Error to mapping Operation on Sale Order.",
        )
        # Change Fiscal Category to test mapping Fiscal Position
        self.sale_order_1.onchange_partner_id()
        self.sale_order_1.onchange_partner_shipping_id()
        self.assertEquals(
            self.sale_order_1.operation_id.name,
            "Venda",
            "Error to mapping correct Operation on Sale Order"
            "after change fiscal category.",
        )
        for line in self.sale_order_1.order_line:
            line._onchange_product_id()
            line._onchange_operation_id()
            line._onchange_operation_line_id()
            line._onchange_fiscal_taxes()
            line.price_unit = 500
            self.assertTrue(
                line.operation_id,
                "Error to mapping Fiscal Position on Sale Order Line.",
            )
            self.assertTrue(
                line.operation_line_id,
                "Error to mapping Fiscal Position on Sale Order Line.",
            )
            if line.operation_line_id.name == 'Revenda':
                self.assertEquals(
                    line.cfop_id.code, '5102',
                    "Error to mappping CFOP 5102"
                    " for Revenda de Contribuinte Dentro do Estado.")
            else:
                self.assertEquals(
                    line.cfop_id.code, '5101',
                    "Error to mapping CFOP 5101"
                    " for Venda de Contribuinte Dentro do Estado.")

            # ICMS
            self.assertEquals(
                line.icms_tax_id.name, 'ICMS 12%',
                "Error to mapping ICMS 12%"
                " for Venda de Contribuinte Dentro do Estado.")
            self.assertEquals(
                line.icms_cst_id.code, '00',
                "Error to mapping CST 00 from ICMS 12%"
                " for Venda de Contribuinte Dentro do Estado.")

            # ICMS FCP
            self.assertFalse(
                line.icmsfcp_tax_id,
                "Error to mapping ICMS FCP 2%"
                " for Venda de Contribuinte Dentro do Estado.")

            # IPI
            if line.operation_line_id.name == 'Revenda':
                self.assertEquals(
                    line.ipi_tax_id.name, 'IPI NT',
                    "Error to mapping IPI NT"
                    " for Revenda de Contribuinte Dentro do Estado.")
                self.assertEquals(
                    line.ipi_cst_id.code, '53',
                    "Error to mapping CST 53 from IPI NT"
                    " to Revenda de Contribuinte Dentro do Estado.")
            else:
                self.assertEquals(
                    line.ipi_tax_id.name, 'IPI 5%',
                    "Error to mapping IPI 5%"
                    " for Venda de Contribuinte Dentro do Estado.")
                self.assertEquals(
                    line.ipi_cst_id.code, '50',
                    "Error to mapping CST 50 from IPI 5%"
                    " to Venda de Contribuinte Dentro do Estado.")

            # PIS
            self.assertEquals(
                line.pis_tax_id.name, 'PIS 0,65%',
                "Error to mapping PIS 0,65%"
                " for Venda de Contribuinte Dentro do Estado.")
            self.assertEquals(
                line.pis_cst_id.code, '01',
                "Error to mapping CST 01 - Operação Tributável com Alíquota"
                " Básica from PIS 0,65% to Venda de Contribuinte Dentro do Estado.")

            # PIS
            self.assertEquals(
                line.cofins_tax_id.name, 'COFINS 3%',
                "Error to mapping COFINS 3%"
                " for Venda de Contribuinte Dentro do Estado.")
            self.assertEquals(
                line.cofins_cst_id.code, '01',
                "Error to mapping CST 01 - Operação Tributável com Alíquota Básica"
                " Básica to COFINS 3% de Venda de Contribuinte Dentro do Estado.")

            # Change Operation Line
            line.operation_line_id = self.operation_line_revenda.id
            self.assertTrue(
                line.operation_id,
                "Error to mapping Fiscal Position on Sale Order Line"
                "after change fiscal category.",
            )
            self.assertEquals(
                line.operation_line_id.name,
                "Revenda",
                "Error to mapping correct Operation Line on Sale Order Line"
                " after change Operation Line.",
            )

        self.sale_order_1.action_confirm()

        # Create and check invoice
        self.sale_order_1.action_invoice_create(final=True)
        self.assertEquals(
            self.sale_order_1.state, "sale", "Error to confirm Sale Order."
        )
        for invoice in self.sale_order_1.invoice_ids:
            self.assertTrue(
                invoice.operation_id,
                "Error to included Operation on invoice"
                " dictionary from Sale Order.",
            )
            self.assertTrue(
                invoice.operation_type,
                "Error to included Operation Type on invoice"
                " dictionary from Sale Order.",
            )
            for line in invoice.invoice_line_ids:
                self.assertTrue(
                    line.operation_line_id,
                    "Error to included Operation Line from Sale Order Line.",
                )

    def test_l10n_br_sale_discount(self):
        """ Test sale discount in l10n_br_sale """
        self.sale_discount = self.sale_object.create(
            dict(
                name="TESTE DESCONTO",
                partner_id=self.env.ref("l10n_br_base.res_partner_akretion").id,
                partner_invoice_id=self.env.ref("l10n_br_base.res_partner_akretion").id,
                partner_shipping_id=self.env.ref(
                    "l10n_br_base.res_partner_akretion"
                ).id,
                user_id=self.env.ref("base.user_demo").id,
                pricelist_id=self.env.ref("product.list0").id,
                team_id=self.env.ref("sales_team.crm_team_1").id,
                state="draft",
                operation_id=self.env.ref('l10n_br_fiscal.fo_venda').id,
                order_line=[
                    (0, 0,
                     dict(
                         name="TESTE DISCOUNT",
                         product_id=self.env.ref("product.product_product_27").id,
                         product_uom_qty=1,
                         product_uom=self.env.ref("uom.product_uom_unit").id,
                         price_unit=100,
                         operation_id=self.env.ref('l10n_br_fiscal.fo_venda').id,
                         operation_line_id=self.env.ref(
                             'l10n_br_fiscal.fo_venda_venda').id
                     ),
                     )
                ],
            )
        )
        self.sale_discount.onchange_partner_id()
        self.sale_discount.onchange_partner_shipping_id()
        self.sale_discount.discount_rate = 10.0
        self.sale_discount.onchange_discount_rate()
        # Test Discount
        self.assertEquals(
            self.sale_discount.amount_total,
            90.0,
            u"Error to apply discount on sale order.",
        )
        for line in self.sale_discount.order_line:
            line._onchange_product_id()
            line._onchange_operation_id()
            line._onchange_operation_line_id()
            line._onchange_fiscal_taxes()
            self.assertTrue(
                line.operation_id,
                "Error to mapping Operantion on Sale Order Line.",
            )
            self.assertTrue(
                line.operation_line_id,
                "Error to mapping Operation Line on Sale Order Line.",
            )
            line.price_unit = 100

        self.sale_discount.action_confirm()
        self.assertTrue(self.sale_discount.state == 'sale')
        self.assertTrue(self.sale_discount.invoice_status == 'to invoice')
        # Create and check invoice
        self.sale_discount.action_invoice_create(final=True)
        for invoice in self.sale_discount.invoice_ids:
            self.assertEquals(
                invoice.amount_untaxed,
                90.0,
                u"Error to apply discount on invoice" u" created from sale order.",
            )
