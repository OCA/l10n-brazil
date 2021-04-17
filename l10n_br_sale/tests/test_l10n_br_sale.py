# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import SavepointCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    TAX_FRAMEWORK_SIMPLES,
    TAX_FRAMEWORK_SIMPLES_ALL,
    TAX_FRAMEWORK_NORMAL,
    CFOP_DESTINATION_INTERNAL,
    CFOP_DESTINATION_EXTERNAL,
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ISSQN,
)


class L10nBrSaleBaseTest(SavepointCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.main_company = self.env.ref('base.main_company')
        self.company = self.env.ref('base.main_company')
        self.so_products = self.env.ref('l10n_br_sale.main_so_only_products')
        self.so_services = self.env.ref('l10n_br_sale.main_so_only_services')
        self.so_product_service = self.env.ref(
            'l10n_br_sale.main_so_product_service')
        self.so_prod_srv = self.env.ref('l10n_br_sale.main_so_product_service')
        self.fsc_op_sale = self.env.ref('l10n_br_fiscal.fo_venda')
        self.fsc_op_line_sale = self.env.ref('l10n_br_fiscal.fo_venda_venda')
        self.fsc_op_line_sale_non_contr = self.env.ref(
            'l10n_br_fiscal.fo_venda_venda_nao_contribuinte')
        self.fsc_op_line_resale = self.env.ref(
            'l10n_br_fiscal.fo_venda_revenda')
        self.fsc_op_line_resale_non_contr = self.env.ref(
            'l10n_br_fiscal.fo_venda_revenda_nao_contribuinte')
        self.fsc_op_line_serv_ind = self.env.ref(
            'l10n_br_fiscal.fo_venda_servico_ind')
        self.fsc_op_line_serv = self.env.ref(
            'l10n_br_fiscal.fo_venda_servico')

        TAXES_NORMAL = {
            'icms': {
                'tax': self.env.ref('l10n_br_fiscal.tax_icms_12'),
                'cst': self.env.ref('l10n_br_fiscal.cst_icms_00'),
            },
            'issqn': {
                'tax': self.env.ref('l10n_br_fiscal.tax_issqn_5'),
            },
            'ipi': {
                'tax': self.env.ref('l10n_br_fiscal.tax_ipi_5'),
                'cst': self.env.ref('l10n_br_fiscal.cst_ipi_50'),
            },
            'pis': {
                'tax': self.env.ref('l10n_br_fiscal.tax_pis_0_65'),
                'cst': self.env.ref('l10n_br_fiscal.cst_pis_01'),
            },
            'cofins': {
                'tax': self.env.ref('l10n_br_fiscal.tax_cofins_3'),
                'cst': self.env.ref('l10n_br_fiscal.cst_cofins_01'),
            },
            'icmsfcp': {
                'tax': False,
                'cst': False,
            },
        }

        TAXES_SIMPLES = {
            'icms': {
                'tax': self.env.ref('l10n_br_fiscal.tax_icms_sn_com_credito'),
                'cst': self.env.ref('l10n_br_fiscal.cst_icmssn_101'),
            },
            'issqn': {
                'tax': self.env.ref('l10n_br_fiscal.tax_issqn_5'),
            },
            'ipi': {
                'tax': self.env.ref('l10n_br_fiscal.tax_ipi_outros'),
                'cst': self.env.ref('l10n_br_fiscal.cst_ipi_99'),
            },
            'pis': {
                'tax': self.env.ref('l10n_br_fiscal.tax_pis_outros'),
                'cst': self.env.ref('l10n_br_fiscal.cst_pis_49'),
            },
            'cofins': {
                'tax': self.env.ref(
                    'l10n_br_fiscal.tax_cofins_outros'),
                'cst': self.env.ref('l10n_br_fiscal.cst_cofins_49'),
            },
            'icmsfcp': {
                'tax': False,
                'cst': False,
            },
        }

        self.FISCAL_DEFS = {
            CFOP_DESTINATION_INTERNAL: {
                self.fsc_op_line_sale.name: {
                    'cfop': self.env.ref('l10n_br_fiscal.cfop_5101'),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                self.fsc_op_line_sale_non_contr.name: {
                    'cfop': self.env.ref('l10n_br_fiscal.cfop_5101'),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                self.fsc_op_line_resale.name: {
                    'cfop': self.env.ref('l10n_br_fiscal.cfop_5102'),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                self.fsc_op_line_resale_non_contr.name: {
                    'cfop': self.env.ref('l10n_br_fiscal.cfop_5102'),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
            },
            CFOP_DESTINATION_EXTERNAL: {
                self.fsc_op_line_sale.name: {
                    'cfop': self.env.ref('l10n_br_fiscal.cfop_6101'),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                self.fsc_op_line_sale_non_contr.name: {
                    'cfop': self.env.ref('l10n_br_fiscal.cfop_6107'),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                self.fsc_op_line_resale.name: {
                    'cfop': self.env.ref('l10n_br_fiscal.cfop_6102'),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
                self.fsc_op_line_resale_non_contr.name: {
                    'cfop': self.env.ref('l10n_br_fiscal.cfop_6108'),
                    TAX_FRAMEWORK_SIMPLES: TAXES_SIMPLES,
                    TAX_FRAMEWORK_NORMAL: TAXES_NORMAL,
                },
            },
            'service': {
                self.fsc_op_line_serv.name: {
                    'cfop': False,
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

    def _run_sale_line_onchanges(self, sale_line):
        sale_line._onchange_product_id_fiscal()
        sale_line._onchange_fiscal_operation_id()
        sale_line._onchange_fiscal_operation_line_id()
        sale_line._onchange_fiscal_taxes()
        sale_line._onchange_discount_percent()

    def _invoice_sale_order(self, sale_order):
        sale_order.action_confirm()

        # Create and check invoice
        sale_order.action_invoice_create(final=True)

        self.assertEquals(
            sale_order.state, "sale", "Error to confirm Sale Order."
        )

        for invoice in sale_order.invoice_ids:
            self.assertTrue(
                invoice.fiscal_operation_id,
                "Error to included Operation on invoice "
                "dictionary from Sale Order.",
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

        self.assertEquals(
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
                line.fiscal_operation_line_id.name]['cfop']

            taxes = self.FISCAL_DEFS[line.cfop_id.destination][
                line.fiscal_operation_line_id.name][
                    line.company_id.tax_framework]

            self.assertEquals(
                line.cfop_id.code, cfop.code,
                "Error to mapping CFOP {} for {}.".format(cfop.code, cfop.name)
            )

            if line.company_id.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
                icms_tax = line.icmssn_tax_id
            else:
                icms_tax = line.icms_tax_id

                if 'Revenda' in line.fiscal_operation_line_id.name:
                    taxes['ipi']['tax'] = self.env.ref(
                        'l10n_br_fiscal.tax_ipi_nt')
                    taxes['ipi']['cst'] = self.env.ref(
                        'l10n_br_fiscal.cst_ipi_53')

            # ICMS
            self.assertEquals(
                icms_tax.name, taxes['icms']['tax'].name,
                "Error to mapping Tax {} for {}.".format(
                    taxes['icms']['tax'].name,
                    line.fiscal_operation_line_id.name)
            )

            self.assertEquals(
                line.icms_cst_id.code, taxes['icms']['cst'].code,
                "Error to mapping CST {} from {} for {}.".format(
                    taxes['icms']['cst'].code,
                    taxes['icms']['tax'].name,
                    line.fiscal_operation_line_id.name)
                )

            # ICMS FCP
            self.assertFalse(
                line.icmsfcp_tax_id,
                "Error to mapping ICMS FCP 2%"
                " for Venda de Contribuinte Dentro do Estado.")

            # IPI
            self.assertEquals(
                line.ipi_tax_id.name, taxes['ipi']['tax'].name,
                "Error to mapping Tax {} for {}.".format(
                    taxes['ipi']['tax'].name,
                    line.fiscal_operation_line_id.name)
            )

            self.assertEquals(
                line.ipi_cst_id.code, taxes['ipi']['cst'].code,
                "Error to mapping CST {} from {} for {}.".format(
                    taxes['ipi']['cst'].code,
                    taxes['ipi']['tax'].name,
                    line.fiscal_operation_line_id.name)
            )

            # PIS
            self.assertEquals(
                line.pis_tax_id.name, taxes['pis']['tax'].name,
                "Error to mapping Tax {} for {}.".format(
                    taxes['pis']['tax'].name,
                    line.fiscal_operation_line_id.name)
            )

            self.assertEquals(
                line.pis_cst_id.code, taxes['pis']['cst'].code,
                "Error to mapping CST {} from {} for {}.".format(
                    taxes['pis']['cst'].code,
                    taxes['pis']['tax'].name,
                    line.fiscal_operation_line_id.name)
            )

            # COFINS
            self.assertEquals(
                line.cofins_tax_id.name, taxes['cofins']['tax'].name,
                "Error to mapping Tax {} for {}.".format(
                    taxes['cofins']['tax'].name,
                    line.fiscal_operation_line_id.name)
            )

            self.assertEquals(
                line.cofins_cst_id.code, taxes['cofins']['cst'].code,
                "Error to mapping CST {} from {} for {}.".format(
                    taxes['cofins']['cst'].code,
                    taxes['cofins']['tax'].name,
                    line.fiscal_operation_line_id.name)
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

        self.assertEquals(
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

            taxes = self.FISCAL_DEFS['service'][
                line.fiscal_operation_line_id.name][
                    line.company_id.tax_framework]

            # ICMS
            if line.tax_icms_or_issqn == TAX_DOMAIN_ICMS:
                if line.company_id.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
                    icms_tax = line.icmssn_tax_id
                else:
                    icms_tax = line.icms_tax_id

                icms_cst = line.icms_cst_id

                self.assertEquals(
                    icms_tax.name, taxes['icms']['tax'].name,
                    "Error to mapping Tax {} for {}.".format(
                        taxes['icms']['tax'].name,
                        line.fiscal_operation_line_id.name)
                )

                self.assertEquals(
                    icms_cst.code, taxes['icms']['cst'].code,
                    "Error to mapping CST {} from {} for {}.".format(
                        taxes['icms']['cst'].code,
                        taxes['icms']['tax'].name,
                        line.fiscal_operation_line_id.name)
                )

                # ICMS FCP
                self.assertFalse(
                    line.icmsfcp_tax_id,
                    "Error to mapping ICMS FCP 2%"
                    " for Venda de Contribuinte Dentro do Estado.")

            if line.tax_icms_or_issqn == TAX_DOMAIN_ISSQN:
                self.assertEquals(
                    line.issqn_tax_id.name, taxes['issqn']['tax'].name,
                    "Error to mapping Tax {} for {}.".format(
                        taxes['issqn']['tax'].name,
                        line.fiscal_operation_line_id.name)
                )

            # PIS
            self.assertEquals(
                line.pis_tax_id.name, taxes['pis']['tax'].name,
                "Error to mapping Tax {} for {}.".format(
                    taxes['pis']['tax'].name,
                    line.fiscal_operation_line_id.name)
            )

            self.assertEquals(
                line.pis_cst_id.code, taxes['pis']['cst'].code,
                "Error to mapping CST {} from {} for {}.".format(
                    taxes['pis']['cst'].code,
                    taxes['pis']['tax'].name,
                    line.fiscal_operation_line_id.name)
            )

            # COFINS
            self.assertEquals(
                line.cofins_tax_id.name, taxes['cofins']['tax'].name,
                "Error to mapping Tax {} for {}.".format(
                    taxes['cofins']['tax'].name,
                    line.fiscal_operation_line_id.name)
            )

            self.assertEquals(
                line.cofins_cst_id.code, taxes['cofins']['cst'].code,
                "Error to mapping CST {} from {} for {}.".format(
                    taxes['cofins']['cst'].code,
                    taxes['cofins']['tax'].name,
                    line.fiscal_operation_line_id.name)
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
        self.so_product_service.action_invoice_create(final=True)
        # Devem existir duas Faturas/Documentos Fiscais
        self.assertEquals(2, self.so_product_service.invoice_count)
