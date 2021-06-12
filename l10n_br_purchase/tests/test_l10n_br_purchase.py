# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree

from odoo.tests import SavepointCase

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
        cls.main_company = cls.env.ref("base.main_company")
        cls.company = cls.env.ref("base.main_company")
        cls.po_products = cls.env.ref("l10n_br_purchase.main_po_only_products")
        # cls.po_services = cls.env.ref(
        #     'l10n_br_purchase.main_po_only_services')
        # cls.po_prod_srv = cls.env.ref(
        #     'l10n_br_purchase.main_po_product_service')
        cls.fsc_op_purchase = cls.env.ref("l10n_br_fiscal.fo_compras")
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

    def _invoice_purchase_order(self, order):
        order.with_context(tracking_disable=True).button_confirm()

        invoice_values = {
            "partner_id": order.partner_id.id,
            "purchase_id": order.id,
            "account_id": order.partner_id.property_account_payable_id.id,
            "type": "in_invoice",
        }

        invoice_values.update(order._prepare_br_fiscal_dict())
        document_type_id = order._context.get("document_type_id")

        if document_type_id:
            document_type = self.env["l10n_br_fiscal.document.type"].browse(
                document_type_id
            )
        else:
            document_type = order.company_id.document_type_id
            document_type_id = order.company_id.document_type_id.id

        document_serie = document_type.get_document_serie(
            order.company_id, order.fiscal_operation_id
        )

        invoice_values["document_serie_id"] = document_serie.id
        invoice_values["document_type_id"] = document_type_id
        invoice_values["issuer"] = DOCUMENT_ISSUER_PARTNER
        self.invoice = (
            self.env["account.invoice"]
            .with_context(tracking_disable=True)
            .create(invoice_values)
        )
        self.invoice.purchase_order_change()

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

            for line in invoice.invoice_line_ids:
                self.assertTrue(
                    line.fiscal_operation_line_id,
                    "Error to included Operation " "Line from Purchase Order Line.",
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
        self._change_user_company(self.main_company)

    def test_fields_view_get(self):
        """Test Purchase Order fields_view_get."""
        view_arch = etree.fromstring(self.po_products.fields_view_get()["arch"])

        self.assertTrue(
            view_arch.findall(".//field[@name='fiscal_operation_id']"),
            "Error to included Operation " "Line from Purchase Order Line.",
        )
