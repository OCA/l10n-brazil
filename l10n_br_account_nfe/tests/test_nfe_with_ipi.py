from odoo.tests import tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestNFeWithIPI(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref)

        cls.configure_normal_company_taxes()
        cls.env.user.groups_id |= cls.env.ref("l10n_br_nfe.group_manager")

        cls.payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "Cash",
                "company_id": cls.company_data["company"].id,
                "payment_method_id": cls.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "fiscal_payment_mode": "18",
                "bank_account_link": "variable",
            }
        )

        # Create the NFe with a product that has a default 5% IPI incidence.
        cls.move_out_venda = cls.init_invoice(
            move_type="out_invoice",
            products=[cls.product_b],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_lc_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_venda")],
            post=False,
        )
        cls.move_out_venda.payment_mode_id = cls.payment_mode
        cls.move_out_venda.action_post()

    def test_nfe_with_ipi(self):
        """
        Test IPI calculation in NFe.
        """
        # Check the IPI percentage and value on the product line
        product_line = self.move_out_venda.invoice_line_ids[0]
        self.assertEqual(product_line.ipi_percent, 5.00)
        self.assertEqual(product_line.ipi_value, 50.00)

        # Check the total values in the NFe
        self.assertEqual(self.move_out_venda.nfe40_vIPI, 50.0)
        self.assertEqual(self.move_out_venda.nfe40_vProd, 1000.00)
        self.assertEqual(self.move_out_venda.nfe40_vNF, 1050.00)
