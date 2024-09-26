# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree

from odoo.tests import Form, SavepointCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    CFOP_DESTINATION_EXTERNAL,
    CFOP_DESTINATION_INTERNAL,
    DOCUMENT_ISSUER_PARTNER,
    TAX_FRAMEWORK_NORMAL,
    TAX_FRAMEWORK_SIMPLES,
    TAX_FRAMEWORK_SIMPLES_ALL,
)


class L10nBrPurchaseBaseTest(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.po_products = cls.env.ref("l10n_br_purchase.lp_po_only_products")
        # cls.po_services = cls.env.ref(
        #     'l10n_br_purchase.main_po_only_services')
        # cls.po_prod_srv = cls.env.ref(
        #     'l10n_br_purchase.main_po_product_service')
        cls.fsc_op_purchase = cls.env.ref("l10n_br_fiscal.fo_compras")
        # Testa os Impostos Dedutiveis
        cls.fsc_op_purchase.deductible_taxes = True
        cls.fsc_op_line_purchase = cls.env.ref("l10n_br_fiscal.fo_compras_compras")
        cls.fsc_op_line_purchase_resale = cls.env.ref(
            "l10n_br_fiscal.fo_compras_compras_comercializacao"
        )
        cls.fsc_op_line_purchase_asset = cls.env.ref(
            "l10n_br_fiscal.fo_compras_compras_ativo"
        )
        cls.fsc_op_line_purchase_use = cls.env.ref(
            "l10n_br_fiscal.fo_compras_compras_uso_consumo"
        )

        cls.fsc_op_line_dist = cls.env.ref("l10n_br_fiscal.fo_compras_compras")
        cls.fsc_op_line_serv = cls.env.ref("l10n_br_fiscal.fo_venda_servico")

        TAXES_NORMAL = {
            "icms": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_icms_12"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_icms_00"),
            },
            "issqn": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_issqn_5"),
            },
            "ipi": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_ipi_5"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_ipi_00"),
            },
            "pis": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_pis_0_65"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_pis_50"),
            },
            "cofins": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_cofins_3"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_pis_50"),
            },
            "icmsfcp": {
                "tax": False,
                "cst": False,
            },
        }

        TAXES_SIMPLES = {
            "icms": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_icms_sn_com_credito"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_icmssn_101"),
            },
            "issqn": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_issqn_5"),
            },
            "ipi": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_ipi_outros"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_ipi_49"),
            },
            "pis": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_pis_outros"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_pis_98"),
            },
            "cofins": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_cofins_outros"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_cofins_98"),
            },
            "icmsfcp": {
                "tax": False,
                "cst": False,
            },
        }

        cls.FISCAL_DEFS = {
            CFOP_DESTINATION_INTERNAL: {
                cls.fsc_op_line_purchase.name: {
                    "cfop": cls.env.ref("l10n_br_fiscal.cfop_1101"),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                cls.fsc_op_line_purchase_resale.name: {
                    "cfop": cls.env.ref("l10n_br_fiscal.cfop_1102"),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                cls.fsc_op_line_purchase_asset.name: {
                    "cfop": cls.env.ref("l10n_br_fiscal.cfop_1551"),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                cls.fsc_op_line_purchase_use.name: {
                    "cfop": cls.env.ref("l10n_br_fiscal.cfop_1556"),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
            },
            CFOP_DESTINATION_EXTERNAL: {
                cls.fsc_op_line_purchase.name: {
                    "cfop": cls.env.ref("l10n_br_fiscal.cfop_2101"),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                cls.fsc_op_line_purchase_resale.name: {
                    "cfop": cls.env.ref("l10n_br_fiscal.cfop_2102"),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                cls.fsc_op_line_purchase_asset.name: {
                    "cfop": cls.env.ref("l10n_br_fiscal.cfop_2551"),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                cls.fsc_op_line_purchase_use.name: {
                    "cfop": cls.env.ref("l10n_br_fiscal.cfop_2556"),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
            },
            "service": {
                cls.fsc_op_line_serv.name: {
                    "cfop": False,
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
            },
        }

    def _change_user_company(self, company):
        self.env.user.company_ids += company
        self.env.user.company_id = company

    def _run_purchase_order_onchanges(self, purchase_order):
        purchase_order.onchange_partner_id()
        purchase_order._onchange_fiscal_operation_id()

    def _run_purchase_line_onchanges(self, purchase_line):
        purchase_line._onchange_product_id_fiscal()
        purchase_line._onchange_fiscal_operation_id()
        purchase_line._onchange_fiscal_operation_line_id()
        purchase_line._onchange_fiscal_taxes()
        purchase_line._onchange_fiscal_tax_ids()

    def _invoice_purchase_order(self, order):
        order.with_context(tracking_disable=True).button_confirm()

        invoice_values = {
            "partner_id": order.partner_id.id,
            "move_type": "in_invoice",
        }

        invoice_values.update(order._prepare_br_fiscal_dict())

        document_type = order.company_id.document_type_id
        document_type_id = order.company_id.document_type_id.id

        document_serie = document_type.get_document_serie(
            order.company_id, order.fiscal_operation_id
        )

        invoice_values["document_serie_id"] = document_serie.id
        invoice_values["document_type_id"] = document_type_id
        invoice_values["issuer"] = DOCUMENT_ISSUER_PARTNER
        self.invoice = (
            self.env["account.move"]
            .with_context(tracking_disable=True)
            .create(invoice_values)
        )

        invoice_lines = self.env["account.move.line"]
        for line in order.order_line:
            invoice_line = invoice_lines.new(
                line._prepare_account_move_line(self.invoice)
            )
            invoice_lines += invoice_line
        self.invoice.invoice_line_ids += invoice_lines
        self.invoice.write({"purchase_id": order.id})
        self.invoice._onchange_purchase_auto_complete()

        self.assertEqual(
            order.order_line.mapped("qty_invoiced"),
            [4.0, 2.0],
            'Purchase: all products should be invoiced"',
        )

        self.assertEqual(order.state, "purchase", "Error to confirm Purchase Order.")

        for invoice in order.invoice_ids:
            self.assertTrue(
                invoice.fiscal_operation_id,
                "Error to included Operation on invoice "
                "dictionary from Purchase Order.",
            )

            self.assertTrue(
                invoice.fiscal_operation_type,
                "Error to included Operation Type on invoice"
                " dictionary from Purchase Order.",
            )

            # Valida os Totais
            self.assertEqual(
                order.amount_total,
                invoice.amount_total,
                "Error field Amount Total in Invoice"
                " are different from Purchase Order.",
            )

            self.assertEqual(
                order.amount_tax,
                invoice.amount_tax,
                "Error field Amount Tax in Invoice are"
                " different from Purchase Order.",
            )
            self.assertEqual(
                order.amount_untaxed,
                invoice.amount_untaxed,
                "Error field Amount Untaxed in Invoice"
                " are different from Purchase Order.",
            )
            self.assertEqual(
                order.amount_price_gross,
                invoice.amount_price_gross,
                "Error field Amount Price Gross in Invoice"
                " are different from Purchase Order.",
            )
            self.assertEqual(
                order.amount_financial_total,
                invoice.amount_financial_total,
                "Error field Amount Financial Total in Invoice"
                " are different from Purchase Order.",
            )
            self.assertEqual(
                order.amount_financial_total_gross,
                invoice.amount_financial_total_gross,
                "Error field Amount Financial Total Gross in Invoice"
                " are different from Purchase Order.",
            )
            self.assertEqual(
                order.amount_freight_value,
                invoice.amount_freight_value,
                "Error field Amount Freight in Invoice are different from "
                "Purchase Order.",
            )
            self.assertEqual(
                order.amount_insurance_value,
                invoice.amount_insurance_value,
                "Error field Amount Insurance in Invoice are different from "
                "Purchase Order.",
            )
            self.assertEqual(
                order.amount_other_value,
                invoice.amount_other_value,
                "Error field Amount Other Values in Invoice are different from "
                "Purchase Order.",
            )

            for line in invoice.invoice_line_ids:
                line._onchange_price_subtotal()
                self.assertTrue(
                    line.fiscal_operation_line_id,
                    "Error to included Operation " "Line from Purchase Order Line.",
                )
                self.assertEqual(
                    line.price_total,
                    line.purchase_line_id.price_total,
                    "Error field Price Total in Invoice Line"
                    " are different from Purchase Order Line.",
                )

        self.invoice_action = order.action_view_invoice()
        self.assertTrue(
            self.invoice_action,
            "Error opening invoice !",
        )

    def test_l10n_br_purchase_products(self):
        """Test brazilian Purchase Order with only Products."""
        self._change_user_company(self.company)
        self._run_purchase_order_onchanges(self.po_products)
        self.assertTrue(
            self.po_products.fiscal_operation_id,
            "Error to mapping Operation on Purchase Order.",
        )

        self.assertEqual(
            self.po_products.fiscal_operation_id.name,
            self.fsc_op_purchase.name,
            "Error to mapping correct Operation on Purchase Order "
            "after change fiscal category.",
        )

        for line in self.po_products.order_line:
            self._run_purchase_line_onchanges(line)

            self.assertTrue(
                line.fiscal_operation_id,
                "Error to mapping Fiscal Operation on Purchase Order Line.",
            )

            self.assertTrue(
                line.fiscal_operation_line_id,
                "Error to mapping Fiscal Operation" " Line on Purchase Order Line.",
            )

            cfop = self.FISCAL_DEFS[line.cfop_id.destination][
                line.fiscal_operation_line_id.name
            ]["cfop"]

            taxes = self.FISCAL_DEFS[line.cfop_id.destination][
                line.fiscal_operation_line_id.name
            ][line.company_id.tax_framework]

            self.assertEqual(
                line.cfop_id.code,
                cfop.code,
                "Error to mapping CFOP {} for {}.".format(cfop.code, cfop.name),
            )

            if line.company_id.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
                icms_tax = line.icmssn_tax_id
            else:
                icms_tax = line.icms_tax_id

            # ICMS
            self.assertEqual(
                icms_tax.name,
                taxes["icms"]["tax"].name,
                "Error to mapping Tax {} for {}.".format(
                    taxes["icms"]["tax"].name, line.fiscal_operation_line_id.name
                ),
            )

            self.assertEqual(
                line.icms_cst_id.code,
                taxes["icms"]["cst"].code,
                "Error to mapping CST {} from {} for {}.".format(
                    taxes["icms"]["cst"].code,
                    taxes["icms"]["tax"].name,
                    line.fiscal_operation_line_id.name,
                ),
            )

            # ICMS FCP
            self.assertFalse(
                line.icmsfcp_tax_id,
                "Error to mapping ICMS FCP 2%"
                " for Venda de Contribuinte Dentro do Estado.",
            )

            # IPI
            self.assertEqual(
                line.ipi_tax_id.name,
                taxes["ipi"]["tax"].name,
                "Error to mapping Tax {} for {}.".format(
                    taxes["ipi"]["tax"].name, line.fiscal_operation_line_id.name
                ),
            )

            self.assertEqual(
                line.ipi_cst_id.code,
                taxes["ipi"]["cst"].code,
                "Error to mapping CST {} from {} for {}.".format(
                    taxes["ipi"]["cst"].code,
                    taxes["ipi"]["tax"].name,
                    line.fiscal_operation_line_id.name,
                ),
            )

            # PIS
            self.assertEqual(
                line.pis_tax_id.name,
                taxes["pis"]["tax"].name,
                "Error to mapping Tax {} for {}.".format(
                    taxes["pis"]["tax"].name, line.fiscal_operation_line_id.name
                ),
            )

            self.assertEqual(
                line.pis_cst_id.code,
                taxes["pis"]["cst"].code,
                "Error to mapping CST {} from {} for {}.".format(
                    taxes["pis"]["cst"].code,
                    taxes["pis"]["tax"].name,
                    line.fiscal_operation_line_id.name,
                ),
            )

            # COFINS
            self.assertEqual(
                line.cofins_tax_id.name,
                taxes["cofins"]["tax"].name,
                "Error to mapping Tax {} for {}.".format(
                    taxes["cofins"]["tax"].name, line.fiscal_operation_line_id.name
                ),
            )

            self.assertEqual(
                line.cofins_cst_id.code,
                taxes["cofins"]["cst"].code,
                "Error to mapping CST {} from {} for {}.".format(
                    taxes["cofins"]["cst"].code,
                    taxes["cofins"]["tax"].name,
                    line.fiscal_operation_line_id.name,
                ),
            )

        self._invoice_purchase_order(self.po_products)

    def test_purchase_report(self):
        """Test Purchase Report"""
        self.env["purchase.report"].read_group(
            [("product_id", "=", self.env.ref("product.product_product_12").id)],
            ["qty_ordered", "price_average:avg"],
            ["product_id"],
        )
        # TODO: Algo a ser validado?

    def test_form_purchase(self):
        """Test Purchase with Form"""

        purchase_form = Form(self.env["purchase.order"])
        purchase_form.partner_id = self.env.ref("l10n_br_base.res_partner_akretion")
        purchase_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_compras")
        with purchase_form.order_line.new() as line:
            line.name = self.env.ref("product.product_product_12").name
            line.product_id = self.env.ref("product.product_product_12")
            line.fiscal_operation_line_id = self.env.ref(
                "l10n_br_fiscal.fo_compras_compras"
            )

        purchase_form.save()

    def test_fields_view_get(self):
        """Test Purchase Order fields_view_get."""
        view_arch = etree.fromstring(self.po_products.fields_view_get()["arch"])

        self.assertTrue(
            view_arch.findall(".//field[@name='fiscal_operation_id']"),
            "Error to included Operation " "Line from Purchase Order Line.",
        )

    def test_fields_freight_insurance_other_costs(self):
        """Test fields Freight, Insurance and Other Costs when
        defined or By Line or By Total in Purchase Order.
        """

        self._change_user_company(self.company)
        # Por padrão a definição dos campos está por Linha
        self.po_products.company_id.delivery_costs = "line"
        self._run_purchase_order_onchanges(self.po_products)
        # Teste definindo os valores Por Linha
        for line in self.po_products.order_line:
            line.price_unit = 100.0
            line.freight_value = 10.0
            line.insurance_value = 10.0
            line.other_value = 10.0
            self._run_purchase_line_onchanges(line)

        self._invoice_purchase_order(self.po_products)

        self.assertEqual(
            self.po_products.amount_freight_value,
            20.0,
            "Unexpected value for the field Amount Freight in Purchase Order.",
        )
        self.assertEqual(
            self.po_products.amount_insurance_value,
            20.0,
            "Unexpected value for the field Amount Insurance in Purchase Order.",
        )
        self.assertEqual(
            self.po_products.amount_other_value,
            20.0,
            "Unexpected value for the field Amount Other in Purchase Order.",
        )

        # Teste definindo os valores Por Total
        # Por padrão a definição dos campos está por Linha
        self.po_products.company_id.delivery_costs = "total"

        # Caso que os Campos na Linha tem valor
        self.po_products.amount_freight_value = 10.0
        self.po_products.amount_insurance_value = 10.0
        self.po_products.amount_other_value = 10.0

        for line in self.po_products.order_line:
            self.assertEqual(
                line.freight_value,
                5.0,
                "Unexpected value for the field Freight in Purchase line.",
            )
            self.assertEqual(
                line.insurance_value,
                5.0,
                "Unexpected value for the field Insurance in Purchase line.",
            )
            self.assertEqual(
                line.other_value,
                5.0,
                "Unexpected value for the field Other Values in Purchase line.",
            )

        # Caso que os Campos na Linha não tem valor
        for line in self.po_products.order_line:
            line.price_unit = 100.0
            line.freight_value = 0.0
            line.insurance_value = 0.0
            line.other_value = 0.0

        self.po_products.company_id.delivery_costs = "total"

        self.po_products.amount_freight_value = 20.0
        self.po_products.amount_insurance_value = 20.0
        self.po_products.amount_other_value = 20.0

        for line in self.po_products.order_line:
            if line.price_total == 440.02:
                self.assertEqual(
                    line.freight_value,
                    13.34,
                    "Unexpected value for the field Amount Freight in Purchase Order.",
                )
                self.assertEqual(
                    line.insurance_value,
                    13.34,
                    "Unexpected value for the field Insurance in Purchase Order.",
                )
                self.assertEqual(
                    line.other_value,
                    13.34,
                    "Unexpected value for the field Other Values in Purchase Order.",
                )

    def test_purchase_service_and_products(self):
        """
        Test Purchase Order with Services and Products.
        """
        # Caso Somente Serviços
        po_only_service = self.env.ref("l10n_br_purchase.main_po_only_service")
        self._run_purchase_order_onchanges(po_only_service)
        for line in po_only_service.order_line:
            self._run_purchase_line_onchanges(line)
        po_only_service.with_context(tracking_disable=True).button_confirm()
        self.assertEqual(
            po_only_service.state, "purchase", "Error to confirm Purchase Order."
        )
        po_only_service.action_create_invoice()
        for invoice in po_only_service.invoice_ids:
            # Caso Internacional não deve ter Documento Fiscal associado
            self.assertTrue(
                invoice.fiscal_document_id,
                "Fiscal Document missing for Purchase with only Service.",
            )

        # Caso Serviços e Produtos
        po_service_product = self.env.ref("l10n_br_purchase.main_po_service_product")
        self._run_purchase_order_onchanges(po_service_product)
        for line in po_service_product.order_line:
            self._run_purchase_line_onchanges(line)
        po_service_product.with_context(tracking_disable=True).button_confirm()
        self.assertEqual(
            po_service_product.state, "purchase", "Error to confirm Purchase Order."
        )
        po_service_product.action_create_invoice()
        for invoice in po_service_product.invoice_ids:
            self.assertTrue(
                invoice.fiscal_document_id,
                "Fiscal Document missing for Purchase with Service and Product.",
            )

    def test_compatible_with_international_case(self):
        """
        Test of compatible with international case, create Invoice but not for Brazil.
        """
        po_international = self.env.ref("purchase.purchase_order_1")
        self._run_purchase_order_onchanges(po_international)
        for line in po_international.order_line:
            line.product_id.purchase_method = "purchase"
            self._run_purchase_line_onchanges(line)
        po_international.with_context(tracking_disable=True).button_confirm()
        po_international.action_create_invoice()
        for invoice in po_international.invoice_ids:
            # Caso Internacional não deve ter Documento Fiscal associado
            self.assertFalse(
                invoice.fiscal_document_id,
                "International case should not has Fiscal Document.",
            )
