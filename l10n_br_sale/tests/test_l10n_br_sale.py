# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import SavepointCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    CFOP_DESTINATION_EXTERNAL,
    CFOP_DESTINATION_INTERNAL,
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ISSQN,
    TAX_FRAMEWORK_NORMAL,
    TAX_FRAMEWORK_SIMPLES,
    TAX_FRAMEWORK_SIMPLES_ALL,
)


class L10nBrSaleBaseTest(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.main_company = cls.env.ref("base.main_company")
        cls.company = cls.env.ref("base.main_company")
        cls.so_products = cls.env.ref("l10n_br_sale.main_so_only_products")
        cls.so_services = cls.env.ref("l10n_br_sale.main_so_only_services")
        cls.so_product_service = cls.env.ref("l10n_br_sale.main_so_product_service")
        cls.so_prod_srv = cls.env.ref("l10n_br_sale.main_so_product_service")
        cls.fsc_op_sale = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.fsc_op_line_sale = cls.env.ref("l10n_br_fiscal.fo_venda_venda")
        cls.fsc_op_line_sale_non_contr = cls.env.ref(
            "l10n_br_fiscal.fo_venda_venda_nao_contribuinte"
        )
        cls.fsc_op_line_resale = cls.env.ref("l10n_br_fiscal.fo_venda_revenda")
        cls.fsc_op_line_resale_non_contr = cls.env.ref(
            "l10n_br_fiscal.fo_venda_revenda_nao_contribuinte"
        )
        cls.fsc_op_line_serv_ind = cls.env.ref("l10n_br_fiscal.fo_venda_servico_ind")
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
                "cst": cls.env.ref("l10n_br_fiscal.cst_ipi_50"),
            },
            "pis": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_pis_0_65"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_pis_01"),
            },
            "cofins": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_cofins_3"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_cofins_01"),
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
                "cst": cls.env.ref("l10n_br_fiscal.cst_ipi_99"),
            },
            "pis": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_pis_outros"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_pis_49"),
            },
            "cofins": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_cofins_outros"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_cofins_49"),
            },
            "icmsfcp": {
                "tax": False,
                "cst": False,
            },
        }

        cls.FISCAL_DEFS = {
            CFOP_DESTINATION_INTERNAL: {
                cls.fsc_op_line_sale.name: {
                    "cfop": cls.env.ref("l10n_br_fiscal.cfop_5101"),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                cls.fsc_op_line_sale_non_contr.name: {
                    "cfop": cls.env.ref("l10n_br_fiscal.cfop_5101"),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                cls.fsc_op_line_resale.name: {
                    "cfop": cls.env.ref("l10n_br_fiscal.cfop_5102"),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                cls.fsc_op_line_resale_non_contr.name: {
                    "cfop": cls.env.ref("l10n_br_fiscal.cfop_5102"),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
            },
            CFOP_DESTINATION_EXTERNAL: {
                cls.fsc_op_line_sale.name: {
                    "cfop": cls.env.ref("l10n_br_fiscal.cfop_6101"),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                cls.fsc_op_line_sale_non_contr.name: {
                    "cfop": cls.env.ref("l10n_br_fiscal.cfop_6107"),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                cls.fsc_op_line_resale.name: {
                    "cfop": cls.env.ref("l10n_br_fiscal.cfop_6102"),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                cls.fsc_op_line_resale_non_contr.name: {
                    "cfop": cls.env.ref("l10n_br_fiscal.cfop_6108"),
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

    def _run_sale_order_onchanges(self, sale_order):
        sale_order.onchange_partner_id()
        sale_order.onchange_partner_shipping_id()
        sale_order._onchange_fiscal_operation_id()
        sale_order.onchange_discount_rate()

    def _run_sale_line_onchanges(self, sale_line):
        sale_line._onchange_product_id_fiscal()
        sale_line._onchange_fiscal_operation_id()
        sale_line._onchange_fiscal_operation_line_id()
        sale_line._onchange_fiscal_taxes()
        sale_line._onchange_discount_percent()

    def _invoice_sale_order(self, sale_order):
        sale_order.action_confirm()

        # Create and check invoice
        sale_order._create_invoices(final=True)

        self.assertEqual(sale_order.state, "sale", "Error to confirm Sale Order.")

        for invoice in sale_order.invoice_ids:
            self.assertTrue(
                invoice.fiscal_operation_id,
                "Error to included Operation on invoice " "dictionary from Sale Order.",
            )

            self.assertTrue(
                invoice.fiscal_operation_type,
                "Error to included Operation Type on invoice"
                " dictionary from Sale Order.",
            )

            for line in invoice.invoice_line_ids:
                self.assertTrue(
                    line.fiscal_operation_line_id,
                    "Error to included Operation Line from Sale Order Line.",
                )

    def test_l10n_br_sale_products(self):
        """Test brazilian Sale Order with only Products."""
        self._change_user_company(self.company)
        self._run_sale_order_onchanges(self.so_products)
        self.assertTrue(
            self.so_products.fiscal_operation_id,
            "Error to mapping Operation on Sale Order.",
        )

        self.assertEqual(
            self.so_products.fiscal_operation_id.name,
            self.fsc_op_sale.name,
            "Error to mapping correct Operation on Sale Order "
            "after change fiscal category.",
        )

        for line in self.so_products.order_line:
            self._run_sale_line_onchanges(line)

            self.assertTrue(
                line.fiscal_operation_id,
                "Error to mapping Fiscal Operation on Sale Order Line.",
            )

            self.assertTrue(
                line.fiscal_operation_line_id,
                "Error to mapping Fiscal Operation Line on Sale Order Line.",
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

            if "Revenda" in line.fiscal_operation_line_id.name:
                taxes["ipi"]["tax"] = self.env.ref("l10n_br_fiscal.tax_ipi_nt")
                taxes["ipi"]["cst"] = self.env.ref("l10n_br_fiscal.cst_ipi_53")

            if (
                "Venda não Contribuinte" in line.fiscal_operation_line_id.name
                and "IPI Outros" in line.ipi_tax_id.name
            ):
                taxes["ipi"]["tax"] = self.env.ref("l10n_br_fiscal.tax_ipi_outros")
                taxes["ipi"]["cst"] = self.env.ref("l10n_br_fiscal.cst_ipi_99")

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

        self._invoice_sale_order(self.so_products)
        self._change_user_company(self.main_company)

    def test_l10n_br_sale_services(self):
        """Test brazilian Sale Order with only Services."""
        self._change_user_company(self.company)
        self._run_sale_order_onchanges(self.so_services)
        self.assertTrue(
            self.so_services.fiscal_operation_id,
            "Error to mapping Operation on Sale Order.",
        )

        self.assertEqual(
            self.so_services.fiscal_operation_id.name,
            self.fsc_op_sale.name,
            "Error to mapping correct Operation on Sale Order "
            "after change fiscal category.",
        )

        for line in self.so_services.order_line:
            self._run_sale_line_onchanges(line)

            self.assertTrue(
                line.fiscal_operation_id,
                "Error to mapping Fiscal Operation on Sale Order Line.",
            )

            self.assertTrue(
                line.fiscal_operation_line_id,
                "Error to mapping Fiscal Operation Line on Sale Order Line.",
            )

            taxes = self.FISCAL_DEFS["service"][line.fiscal_operation_line_id.name][
                line.company_id.tax_framework
            ]

            # ICMS
            if line.tax_icms_or_issqn == TAX_DOMAIN_ICMS:
                if line.company_id.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
                    icms_tax = line.icmssn_tax_id
                else:
                    icms_tax = line.icms_tax_id

                icms_cst = line.icms_cst_id

                self.assertEqual(
                    icms_tax.name,
                    taxes["icms"]["tax"].name,
                    "Error to mapping Tax {} for {}.".format(
                        taxes["icms"]["tax"].name, line.fiscal_operation_line_id.name
                    ),
                )

                self.assertEqual(
                    icms_cst.code,
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

            if line.tax_icms_or_issqn == TAX_DOMAIN_ISSQN:
                self.assertEqual(
                    line.issqn_tax_id.name,
                    taxes["issqn"]["tax"].name,
                    "Error to mapping Tax {} for {}.".format(
                        taxes["issqn"]["tax"].name, line.fiscal_operation_line_id.name
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

        self._invoice_sale_order(self.so_services)
        self._change_user_company(self.main_company)

    def test_l10n_br_sale_product_service(self):
        """Test brazilian Sale Order with Product and Service."""
        self._run_sale_order_onchanges(self.so_product_service)
        for line in self.so_product_service.order_line:
            self._run_sale_line_onchanges(line)

        self.so_product_service.action_confirm()
        # Create and check invoice
        self.so_product_service._create_invoices(final=True)
        # Devem existir duas Faturas/Documentos Fiscais
        self.assertEqual(2, self.so_product_service.invoice_count)

    def test_fields_freight_insurance_other_costs(self):
        """Test fields Freight, Insurance and Other Costs when
        defined or By Line or By Total in Sale Order.
        """

        # Por padrão a definição dos campos está por Linha
        self.so_products.company_id.delivery_costs = "line"
        # Teste definindo os valores Por Linha
        for line in self.so_products.order_line:
            line.price_unit = 100.0
            line.freight_value = 10.0
            line.insurance_value = 10.0
            line.other_value = 10.0

        self.so_products.action_confirm()

        self.assertEqual(
            self.so_products.amount_freight_value,
            20.0,
            "Unexpected value for the field Amount Freight in Sale Order.",
        )
        self.assertEqual(
            self.so_products.amount_insurance_value,
            20.0,
            "Unexpected value for the field Amount Insurance in Sale Order.",
        )
        self.assertEqual(
            self.so_products.amount_other_value,
            20.0,
            "Unexpected value for the field Amount Other in Sale Order.",
        )

        # Teste definindo os valores Por Total
        # Por padrão a definição dos campos está por Linha
        self.so_products.company_id.delivery_costs = "total"

        # Caso que os Campos na Linha tem valor
        self.so_products.amount_freight_value = 10.0
        self.so_products.amount_insurance_value = 10.0
        self.so_products.amount_other_value = 10.0

        for line in self.so_products.order_line:

            self.assertEqual(
                line.freight_value,
                5.0,
                "Unexpected value for the field Freight in Sale line.",
            )
            self.assertEqual(
                line.insurance_value,
                5.0,
                "Unexpected value for the field Insurance in Sale line.",
            )
            self.assertEqual(
                line.other_value,
                5.0,
                "Unexpected value for the field Other Values in Sale line.",
            )

        # Caso que os Campos na Linha não tem valor
        for line in self.so_products.order_line:
            line.price_unit = 100.0
            line.freight_value = 0.0
            line.insurance_value = 0.0
            line.other_value = 0.0

        self.so_products.company_id.delivery_costs = "total"

        self.so_products.amount_freight_value = 20.0
        self.so_products.amount_insurance_value = 20.0
        self.so_products.amount_other_value = 20.0

        self.so_products.action_confirm()

        for line in self.so_products.order_line:
            if line.price_total == 234.29:
                self.assertEqual(
                    line.freight_value,
                    11.43,
                    "Unexpected value for the field Amount Freight in Sale Order.",
                )
                self.assertEqual(
                    line.insurance_value,
                    11.43,
                    "Unexpected value for the field Insurance in Sale line.",
                )
                self.assertEqual(
                    line.other_value,
                    11.43,
                    "Unexpected value for the field Other Values in Sale line.",
                )
