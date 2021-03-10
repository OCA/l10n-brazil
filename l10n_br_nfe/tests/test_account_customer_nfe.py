# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.tests.common import TransactionCase


class TestCustomerNFe(TransactionCase):
    def setUp(self):
        super(TestCustomerNFe, self).setUp()
        self.invoice_same_state = self.env.ref(
            "l10n_br_account_product.demo_nfe_same_state"
        )
        self.invoice_other_costs = self.env.ref(
            "l10n_br_account_product.demo_nfe_other_costs"
        )
        self.invoice_difal = self.env.ref("l10n_br_account_product.demo_nfe_difal")

    def test_customer_nfe_same_state(self):
        """Test customer NFe same state 'Contribuinte' """
        self.invoice_same_state._onchange_fiscal_document_id()
        assert self.invoice_same_state.document_serie_id, (
            "Error with _onchange_fiscal_document_id() field "
            "document_serie_id is not mapped."
        )
        self.invoice_same_state._onchange_fiscal()
        assert self.invoice_same_state.fiscal_position_id, (
            "Error with _onchange_fiscal() method, field "
            "fiscal_position_id is not mapped."
        )
        self.assertEquals(
            self.invoice_same_state.state, "draft", "Invoice is not in Draft state."
        )

        for line in self.invoice_same_state.invoice_line_ids:
            line._onchange_fiscal()
            assert line.fiscal_position_id, (
                "Error with _onchange_fiscal() method in object"
                " account.invoice.line, field fiscal_position_id"
                " is not mapped."
            )
            assert line.cfop_id, (
                "Error with _onchange_fiscal() method in object"
                " account.invoice.line, field cfop_id"
                " is not mapped."
            )
            assert line.invoice_line_tax_ids, (
                "Error with _onchange_fiscal() method in object"
                " account.invoice.line, field invoice_line_tax_ids"
                " is not mapped."
            )
            # Check ICMS
            self.assertEquals(line.icms_cst_id.code, "00", "ICMS CST is not 00")
            self.assertEquals(line.icms_base, 1000.0, "ICMS Base is not 1000.0 ")
            self.assertEquals(line.icms_base_other, 0.0, "Other ICMS Base is not 0.0 ")
            self.assertEquals(line.icms_value, 180.0, "ICMS Value is not 180.0 ")
            self.assertEquals(line.icms_percent, 18.0, "ICMS Percent is not 18")
            self.assertEquals(
                line.icms_percent_reduction, 0.0, "ICMS Percent Reduction is not 0.0 "
            )

            # Check ICMS ST
            self.assertEquals(line.icms_st_base, 0.0, "ICMS ST BASE is not 0.0")
            self.assertEquals(
                line.icms_st_base_other, 0.0, "Other ICMS ST BASE is not 0.0"
            )
            self.assertEquals(line.icms_st_value, 0.0, "ICMS ST Value is not 0.0")
            self.assertEquals(line.icms_st_percent, 0.0, "ICMS ST Percent is not 0.0")
            self.assertEquals(
                line.icms_st_percent_reduction,
                0.0,
                "ICMS ST Percent Reduction is not 0.0",
            )

            # Check IPI
            self.assertEquals(line.ipi_cst_id.code, "50", "IPI CODE is not 50")
            self.assertEquals(line.ipi_base, 1000.0, "ICMS ST Value is not 1000.0")
            self.assertEquals(line.ipi_base_other, 0.0, "Other IPI Base is not 0.0 ")
            self.assertEquals(line.ipi_value, 150.0, "ICMS Value is not 150.0 ")
            self.assertEquals(line.ipi_percent, 15.0, "ICMS Percent is not 15 .")

            # Check PIS
            self.assertEquals(line.pis_cst_id.code, "01", "PIS CODE is not 01")
            self.assertEquals(line.pis_base, 1000.0, "PIS BASE is not 1000.0")
            self.assertEquals(line.pis_value, 6.50, "PIS Value is not 6.50 ")
            self.assertEquals(line.pis_percent, 0.65, "ICMS Percent is not 0.65 .")

            # Check COFINS
            self.assertEquals(line.cofins_cst_id.code, "01", "COFINS CODE is not 01")
            self.assertEquals(line.cofins_base, 1000.0, "COFINS BASE is not 1000.0")
            self.assertEquals(line.cofins_value, 30.0, "COFINS Value is not 30.0 ")
            self.assertEquals(line.cofins_percent, 3.0, "ICMS Percent is not 3.0 .")

        self.invoice_same_state.with_context(
            {"fiscal_document_code": "55"}
        ).action_invoice_open()
        self.assertEquals(
            self.invoice_same_state.state,
            "sefaz_export",
            "Invoice should be in state SEFAZ EXPORT",
        )

        self.assertEquals(
            self.invoice_same_state.amount_gross, 2000.0, "Amount Gross is not 2000.0"
        )
        self.assertEquals(
            self.invoice_same_state.amount_discount, 0.0, "Amount Discount is not 0.0"
        )
        self.assertEquals(
            self.invoice_same_state.amount_untaxed,
            2000.0,
            "Amount Untaxed is not 2000.0",
        )
        self.assertEquals(
            self.invoice_same_state.amount_tax, 0.0, "Amount Untaxed is not 0.0"
        )
        self.assertEquals(
            self.invoice_same_state.amount_total, 2000.0, "Amount Total is not 2000.0"
        )
        self.assertEquals(
            self.invoice_same_state.residual, 2000.0, "Amount Residual is not 2000.0"
        )

        # Deveria existir algo ?
        for tax in self.invoice_same_state.tax_line_ids:
            if tax.base_code_id.domain == "ipi":
                self.assertEquals(tax.base, 2000.0, "IPI BASE is not 2000.0")

        # TOTAL IPI
        self.assertEquals(
            self.invoice_same_state.ipi_base, 2000.0, "IPI Total Base is not 1000.0"
        )
        self.assertEquals(
            self.invoice_same_state.ipi_value, 300.0, "ICMS Total Value is not 300.0 "
        )

        # TOTAL ICMS
        self.assertEquals(
            self.invoice_same_state.icms_base, 2000.0, "ICMS Total Base is not 1000.0 "
        )
        self.assertEquals(
            self.invoice_same_state.icms_value, 360.0, "ICMS Total Value is not 360.0 "
        )

        # Total PIS
        self.assertEquals(
            self.invoice_same_state.pis_base, 2000.0, "PIS Total BASE is not 1000.0"
        )
        self.assertEquals(
            self.invoice_same_state.pis_value, 13.0, "PIS Total Value is not 13.0 "
        )

        # Total COFINS
        self.assertEquals(
            self.invoice_same_state.cofins_base,
            2000.0,
            "COFINS Total Base is not 1000.0",
        )
        self.assertEquals(
            self.invoice_same_state.cofins_value,
            60.0,
            "COFINS Total Value is not 60.0 ",
        )

    def test_customer_invoice_other_costs(self):
        """Test customer NFe other costs 'Contribuinte' """
        self.invoice_other_costs._onchange_fiscal_document_id()
        self.invoice_other_costs._onchange_fiscal()
        for line in self.invoice_other_costs.invoice_line_ids:
            line._onchange_fiscal()
            self.assertEquals(
                line.freight_value, 100.0, "Freight value is not 100.0")
            self.assertEquals(
                line.insurance_value, 10.0, "Insurance value is not 10.0")
            self.assertEquals(
                line.other_value, 10.0, "Other Costs value is not 10.0")

        self.invoice_other_costs.with_context(
            {"fiscal_document_code": "55"}
        ).action_invoice_open()
        self.assertEquals(
            self.invoice_other_costs.amount_freight_value,
            100.0,
            "Amount Freight is not 100.0",
        )
        self.assertEquals(
            self.invoice_other_costs.amount_insurance_value,
            10.0,
            "Amount Insurance is not 10.0",
        )
        self.assertEquals(
            self.invoice_other_costs.amount_other_value,
            10.0,
            "Amount Costs is not 10.0",
        )

    def test_customer_invoice_difal(self):
        """Test customer NFe with DIFAL 'Nao Contribuinte' """
        self.invoice_difal._onchange_fiscal_document_id()
        self.invoice_difal._onchange_fiscal()
        self.invoice_difal._onchange_partner_id()
        self.invoice_difal._onchange_journal_id()
        self.invoice_difal._onchange_payment_term_date_invoice()

        for line in self.invoice_difal.invoice_line_ids:
            line._onchange_fiscal()
            line._check_partner_order_line()
            line._onchange_tax_icms()
            line._onchange_tax_icms_st()
            line._onchange_tax_ipi()
            line._onchange_tax_pis()
            line._onchange_tax_cofins()

            assert line.fiscal_position_id, (
                "Error with _onchange_fiscal() method in object"
                " account.invoice.line, field fiscal_position_id"
                " is not mapped."
            )
            assert line.cfop_id, (
                "Error with _onchange_fiscal() method in object"
                " account.invoice.line, field cfop_id"
                " is not mapped."
            )
            assert line.invoice_line_tax_ids, (
                "Error with _onchange_fiscal() method in object"
                " account.invoice.line, field invoice_line_tax_ids"
                " is not mapped."
            )

            # Check ICMS
            self.assertEquals(line.icms_cst_id.code, "00", "ICMS CST is not 00")
            self.assertEquals(line.icms_base, 1120.0, "ICMS Base is not 1120.0 ")
            self.assertEquals(line.icms_base_other, 0.0, "Other ICMS Base is not 0.0 ")
            self.assertEquals(line.icms_value, 134.4, "ICMS Value is not 134.4 ")
            self.assertEquals(line.icms_percent, 12.0, "ICMS Percent is not 12")
            self.assertEquals(
                line.icms_percent_reduction, 0.0, "ICMS Percent Reduction is not 0.0 "
            )

            # Check ICMS DIFAL
            self.assertEquals(
                line.icms_dest_base, 1120.0, "ICMS Dest Base is not 1120.0 "
            )
            self.assertEquals(
                line.icms_fcp_percent, 2.0, "ICMS FCP Percent is not 2.0% "
            )
            self.assertEquals(
                line.icms_dest_percent, 0.18, "ICMS Dest Percent is not 0.18 "
            )
            self.assertEquals(
                line.icms_origin_percent, 12.0, "ICMS Origin Percent is not 12.0% "
            )
            self.assertEquals(
                line.icms_part_percent, 1, "ICMS Origin Percent is not 1.0% "
            )
            self.assertEquals(line.icms_fcp_value, 22.4, "ICMS FCP Value is not 22.4 ")
            self.assertEquals(
                line.icms_dest_value, 132.38, "ICMS Dest Value is not 132.38 "
            )
            self.assertEquals(
                line.icms_origin_value, 0.0, "ICMS Origin Value is not 0.0"
            )

            # Check ICMS ST
            self.assertEquals(line.icms_st_base, 0.0, "ICMS ST BASE is not 0.0")
            self.assertEquals(
                line.icms_st_base_other, 0.0, "Other ICMS ST BASE is not 0.0"
            )
            self.assertEquals(line.icms_st_value, 0.0, "ICMS ST Value is not 0.0")
            self.assertEquals(line.icms_st_percent, 0.0, "ICMS ST Percent is not 0.0")
            self.assertEquals(
                line.icms_st_percent_reduction,
                0.0,
                "ICMS ST Percent Reduction is not 0.0",
            )

            # Check IPI
            self.assertEquals(line.ipi_cst_id.code, "50", "IPI CODE is not 50")
            self.assertEquals(line.ipi_base, 1000.0, "ICMS ST Value is not 1000.0")
            self.assertEquals(line.ipi_base_other, 0.0, "Other IPI Base is not 0.0 ")
            self.assertEquals(line.ipi_value, 150.0, "ICMS Value is not 150.0 ")
            self.assertEquals(line.ipi_percent, 15.0, "ICMS Percent is not 15 .")

            # Check COFINS
            self.assertEquals(line.cofins_cst_id.code, "01", "COFINS CODE is not 01")
            self.assertEquals(line.cofins_base, 1000.0, "COFINS BASE is not 1000.0")
            self.assertEquals(line.cofins_value, 30.0, "COFINS Value is not 30.0 ")
            self.assertEquals(line.cofins_percent, 3.0, "ICMS Percent is not 3.0 .")
