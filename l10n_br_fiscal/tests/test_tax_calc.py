# @ 2021 KMEE - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestTaxCalc(TransactionCase):
    def setUp(self):
        super(TestTaxCalc, self).setUp()

        self.fiscal_document_demo_1 = self.env.ref("l10n_br_fiscal.demo_nfe_same_state")
        self.fiscal_sale_operation = self.env.ref("l10n_br_fiscal.fo_venda")

    def test_tax_engine_automatic(self):
        """
        In the test cases that have been added, it's only checked that the tax values
            were loaded correctly based on the 'tax_calc' selected for that operation
            and the module's demo data.

        Standard behavior of the system, where as soon as a product is selected,
            all taxes referring to it are already loaded - usually linked to the
            NCM.
        """
        product = self.fiscal_document_demo_1.line_ids[0]
        product._onchange_fiscal_operation_id()

        self.assertEqual(
            product.icms_percent,
            12.0,
            "The ICMS percent does not match the standard in product from Automatic "
            "Tax Engine.",
        )
        self.assertEqual(
            product.icms_value,
            12.0,
            "The ICMS value does not match the standard in product from Automatic Tax "
            "Engine.",
        )

        self.assertEqual(
            product.ipi_percent,
            0.0,
            "The IPI percent does not match the standard in product from Automatic Tax "
            "Engine.",
        )
        self.assertEqual(
            product.ipi_value,
            0.0,
            "The IPI value does not match the standard in product from Automatic Tax "
            "Engine.",
        )

        self.assertEqual(
            product.pis_percent,
            0.65,
            "The PIS percent does not match the standard in product from Automatic Tax "
            "Engine.",
        )
        self.assertEqual(
            product.pis_value,
            0.65,
            "The PIS value does not match the standard in product from Automatic Tax "
            "Engine.",
        )

        self.assertEqual(
            product.cofins_percent,
            3.0,
            "The Cofins percent does not match the standard in product from Automatic "
            "Tax Engine.",
        )
        self.assertEqual(
            product.cofins_value,
            3.0,
            "The Cofins value does not match the standard in product from Automatic "
            "Tax Engine.",
        )

    def test_tax_engine_semi_automatic(self):
        """
        Unlike the default behavior of the system, when the 'tax_calc' is set to
            semi-automatic, the user must select the rates that will be used on
            that product and only then the system will calculate them.
        """

        self.fiscal_sale_operation["tax_calc"] = "tax_calc_only"

        fiscal_document = self.env["l10n_br_fiscal.document"].create(
            dict(
                fiscal_operation_id=self.fiscal_sale_operation.id,
                document_type_id=self.env.ref("l10n_br_fiscal.document_55").id,
                document_serie_id=self.env.ref(
                    "l10n_br_fiscal.empresa_lc_document_55_serie_1"
                ).id,
                company_id=self.env.ref("l10n_br_base.empresa_lucro_presumido").id,
                document_serie=1,
                partner_id=self.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                user_id=self.env.ref("base.user_demo").id,
                fiscal_operation_type="in",
                line_ids=[
                    (
                        0,
                        0,
                        {
                            "name": "Teste - Cálculo Semi-Automático",
                            "product_id": self.env.ref("product.product_product_6").id,
                            "uom_id": self.env.ref("uom.product_uom_unit").id,
                            "price_unit": 100,
                            "quantity": 1,
                            "fiscal_operation_type": "in",
                            "fiscal_operation_id": self.fiscal_sale_operation.id,
                            "fiscal_operation_line_id": self.env.ref(
                                "l10n_br_fiscal.fo_venda_venda"
                            ).id,
                            "icms_tax_id": self.env.ref(
                                "l10n_br_fiscal.tax_icms_12"
                            ).id,
                            "ipi_tax_id": self.env.ref("l10n_br_fiscal.tax_ipi_nt").id,
                            "cofins_tax_id": self.env.ref(
                                "l10n_br_fiscal.tax_cofins_3"
                            ).id,
                            "pis_tax_id": self.env.ref(
                                "l10n_br_fiscal.tax_pis_0_65"
                            ).id,
                        },
                    )
                ],
            )
        )

        product = fiscal_document.line_ids[0]
        product._onchange_fiscal_taxes()
        product._onchange_fiscal_operation_id()

        self.assertEqual(
            product.icms_percent,
            12.0,
            "The ICMS percent does not match the standard in product from "
            "Semi-Automatic Tax Engine.",
        )
        self.assertEqual(
            product.icms_value,
            12.0,
            "The ICMS value does not match the standard in product from Semi-Automatic "
            "Tax Engine.",
        )

        self.assertEqual(
            product.ipi_percent,
            0.0,
            "The IPI percent does not match the standard in product from "
            "Semi-Automatic Tax Engine.",
        )
        self.assertEqual(
            product.ipi_value,
            0.0,
            "The IPI value does not match the standard in product from Semi-Automatic "
            "Tax Engine.",
        )

        self.assertEqual(
            product.pis_percent,
            0.65,
            "The PIS percent does not match the standard in product from "
            "Semi-Automatic Tax Engine.",
        )
        self.assertEqual(
            product.pis_value,
            0.65,
            "The PIS value does not match the standard in product from Semi-Automatic "
            "Tax Engine.",
        )

        self.assertEqual(
            product.cofins_percent,
            3.0,
            "The Cofins percent does not match the standard in product from "
            "Semi-Automatic Tax Engine.",
        )
        self.assertEqual(
            product.cofins_value,
            3.0,
            "The Cofins value does not match the standard in product from "
            "Semi-Automatic Tax Engine.",
        )

    def test_tax_engine_manual(self):
        """
        Unlike the other options, when 'tax_calc' is set to manual, it's the user's
            responsibility to enter all tax information into the system. He can
            register this option in any of the operations, not being restricted to
            anything.
        """
        self.fiscal_sale_operation["tax_calc"] = "tax_calc_manual"

        fiscal_document = self.env["l10n_br_fiscal.document"].create(
            dict(
                fiscal_operation_id=self.fiscal_sale_operation.id,
                document_type_id=self.env.ref("l10n_br_fiscal.document_55").id,
                document_serie_id=self.env.ref(
                    "l10n_br_fiscal.empresa_lc_document_55_serie_1"
                ).id,
                company_id=self.env.ref("l10n_br_base.empresa_lucro_presumido").id,
                document_serie=1,
                partner_id=self.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                user_id=self.env.ref("base.user_demo").id,
                fiscal_operation_type="in",
                line_ids=[
                    (
                        0,
                        0,
                        {
                            "name": "Teste - Cálculo Manual",
                            "product_id": self.env.ref("product.product_product_6").id,
                            "uom_id": self.env.ref("uom.product_uom_unit").id,
                            "price_unit": 100,
                            "quantity": 1,
                            "fiscal_operation_type": "in",
                            "fiscal_operation_id": self.fiscal_sale_operation.id,
                            "fiscal_operation_line_id": self.env.ref(
                                "l10n_br_fiscal.fo_venda_venda"
                            ).id,
                            "icms_cst_id": self.env.ref(
                                "l10n_br_fiscal.cst_icms_00"
                            ).id,
                            "icms_base": 1000.0,
                            "icms_percent": 15.0,
                            "icms_value": 150.0,
                            "ipi_cst_id": self.env.ref("l10n_br_fiscal.cst_ipi_49").id,
                            "ipi_base": 1000.0,
                            "ipi_percent": 20.0,
                            "ipi_value": 200.0,
                            "pis_cst_id": self.env.ref("l10n_br_fiscal.cst_pis_01").id,
                            "pis_base": 1000.0,
                            "pis_percent": 5.0,
                            "pis_value": 50.0,
                            "cofins_cst_id": self.env.ref(
                                "l10n_br_fiscal.cst_cofins_01"
                            ).id,
                            "cofins_base": 1000.0,
                            "cofins_percent": 2.0,
                            "cofins_value": 20.0,
                        },
                    ),
                ],
            )
        )

        product = fiscal_document.line_ids[0]
        product._onchange_fiscal_operation_id()

        icms_value = product.icms_base * (product.icms_percent / 100)
        self.assertEqual(
            product.icms_value,
            icms_value,
            "The value of ICMS is not the same. Error in manual demo data entry.",
        )

        ipi_value = product.ipi_base * (product.ipi_percent / 100)
        self.assertEqual(
            product.ipi_value,
            ipi_value,
            "The value of IPI is not the same. Error in manual demo data entry.",
        )

        pis_value = product.pis_base * (product.pis_percent / 100)
        self.assertEqual(
            product.pis_value,
            pis_value,
            "The value of PIS is not the same. Error in manual demo data entry.",
        )

        cofins_value = product.cofins_base * (product.cofins_percent / 100)
        self.assertEqual(
            product.cofins_value,
            cofins_value,
            "The value of Cofins is not the same. Error in manual demo data entry.",
        )
