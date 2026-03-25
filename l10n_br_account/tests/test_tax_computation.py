# Copyright 2025-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

"""
Unit tests for Brazilian tax computation behavior.

These tests capture the expected behavior of tax computation in l10n_br_account
to serve as a specification for refactoring to Odoo 18.0+.

The key behaviors tested:
1. compute_all with Brazilian fiscal parameters
2. Tax line creation and balancing
3. Integration between account.tax and l10n_br_fiscal.tax
4. Fiscal document field propagation to tax computation
"""

import logging

from odoo import Command
from odoo.tests import TransactionCase, tagged

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestBrazilianTaxComputation(TransactionCase):
    """
    Test Brazilian tax computation behavior to establish a baseline
    for Odoo 18.0 refactoring.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.env.user.company_id = cls.company

        # Get test products
        cls.product_a = cls.env.ref("l10n_br_fiscal.customized_development_sale")
        # Use a different product that exists in demo data
        cls.product_b = cls.env.ref("product.product_product_7")

        # Get fiscal operations
        cls.fo_venda = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.fo_venda_revenda = cls.env.ref("l10n_br_fiscal.fo_venda_revenda")

        # Get partner
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")

    def test_01_compute_all_with_fiscal_parameters(self):
        """
        Test that compute_all accepts and uses Brazilian fiscal parameters.

        This is the core method that integrates Brazilian fiscal taxes with
        Odoo's account.tax system. It should:
        1. Accept fiscal_taxes, cfop, ncm, etc. parameters
        2. Compute taxes using the Brazilian fiscal engine
        3. Return results in the standard Odoo format with Brazilian amounts
        """
        # Get an ICMS tax
        icms_tax = self.env.ref("l10n_br_fiscal.tax_icms_12")

        # Find corresponding account.tax
        account_tax = self.env["account.tax"].search(
            [
                ("company_id", "=", self.company.id),
                ("name", "like", "ICMS Saída"),
            ],
            limit=1,
        )

        self.assertTrue(account_tax, "ICMS account tax should exist")

        # Test compute_all with Brazilian parameters
        result = account_tax.compute_all(
            price_unit=100.0,
            currency=self.company.currency_id,
            quantity=1.0,
            product=self.product_a,
            partner=self.partner,
            is_refund=False,
            handle_price_include=True,
            include_caba_tags=False,
            fixed_multiplicator=1,
            # Brazilian fiscal parameters
            fiscal_taxes=icms_tax,
            operation_line=self.fo_venda.line_ids[0],
            cfop=self.env.ref("l10n_br_fiscal.cfop_5101"),
            ncm=self.product_a.ncm_id,
            discount_value=0.0,
            insurance_value=0.0,
            other_value=0.0,
            freight_value=0.0,
        )

        # Verify result structure
        self.assertIn("total_excluded", result)
        self.assertIn("total_included", result)
        self.assertIn("taxes", result)
        self.assertIn("base_tags", result)

        _logger.info(f"compute_all result: {result}")

    def test_02_invoice_line_tax_creation(self):
        """
        Test that invoice lines create proper tax lines with Brazilian taxes.

        When creating an invoice with fiscal_operation_id:
        1. Tax lines (display_type='tax') should be created
        2. Tax amounts should be computed using Brazilian fiscal rules
        3. The entry should balance (debit = credit)
        """
        # Create a simple invoice
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "fiscal_operation_id": self.fo_venda.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "fiscal_operation_id": self.fo_venda.id,
                            "fiscal_operation_line_id": self.fo_venda.line_ids[0].id,
                        }
                    )
                ],
            }
        )

        # Check that tax lines were created
        tax_lines = invoice.line_ids.filtered(lambda line: line.display_type == "tax")
        _logger.info(f"Created {len(tax_lines)} tax lines")

        # Check that entry is balanced
        total_debit = sum(invoice.line_ids.mapped("debit"))
        total_credit = sum(invoice.line_ids.mapped("credit"))
        # Use assertAlmostEqual to handle floating point precision
        self.assertAlmostEqual(
            total_debit,
            total_credit,
            places=10,
            msg=f"Entry not balanced: debit={total_debit}, credit={total_credit}",
        )

        _logger.info(f"Invoice totals - debit: {total_debit}, credit: {total_credit}")

    def test_03_compute_all_tax_field(self):
        """
        Test the _compute_all_tax method on account.move.line.

        This method computes taxes and stores them in compute_all_tax field,
        which is used by the dynamic line sync to create tax lines.

        In Odoo 18, this field and method don't exist, so we need to understand
        what data structure it produces.
        """
        # Create an invoice line
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "fiscal_operation_id": self.fo_venda.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "fiscal_operation_id": self.fo_venda.id,
                            "fiscal_operation_line_id": self.fo_venda.line_ids[0].id,
                        }
                    )
                ],
            }
        )

        # Get the product line
        product_line = invoice.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        )
        self.assertTrue(product_line, "Product line should exist")

        # Trigger _compute_all_tax
        product_line._compute_all_tax()

        # Check the compute_all_tax field structure
        compute_all_tax = product_line.compute_all_tax
        _logger.info(f"compute_all_tax type: {type(compute_all_tax)}")
        _logger.info(f"compute_all_tax value: {compute_all_tax}")

        # The field should be a dict with frozendict keys
        self.assertIsInstance(compute_all_tax, dict)

    def test_04_fiscal_tax_integration(self):
        """
        Test that fiscal taxes (l10n_br_fiscal.tax) integrate with account taxes.

        The account.tax records should have fiscal_tax_ids related field
        pointing to the corresponding fiscal taxes.
        """
        # Get account tax
        account_tax = self.env["account.tax"].search(
            [
                ("company_id", "=", self.company.id),
                ("name", "like", "ICMS Saída"),
            ],
            limit=1,
        )

        self.assertTrue(account_tax, "Account tax should exist")

        # Check fiscal_tax_ids
        fiscal_taxes = account_tax.fiscal_tax_ids
        _logger.info(
            f"Account tax {account_tax.name} has {len(fiscal_taxes)} fiscal taxes"
        )

        # At least one fiscal tax should exist
        self.assertTrue(fiscal_taxes, "Account tax should have related fiscal taxes")

    def test_05_tax_repartition_lines_setup(self):
        """
        Test that taxes have proper repartition lines with accounts.

        For Brazilian taxes to work correctly:
        1. Invoice repartition lines should have account_id set
        2. Refund repartition lines should have account_id set
        3. Factor percent should be correct (-100 for deductible/withholdable)
        """
        # Get ICMS tax
        account_tax = self.env["account.tax"].search(
            [
                ("company_id", "=", self.company.id),
                ("name", "like", "ICMS Saída"),
            ],
            limit=1,
        )

        self.assertTrue(account_tax, "ICMS tax should exist")

        # Check invoice repartition lines
        invoice_rep_lines = account_tax.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )

        for line in invoice_rep_lines:
            _logger.info(
                f"Invoice rep line: account={line.account_id.name}, "
                f"factor={line.factor_percent}"
            )
            # Tax lines should have an account
            self.assertTrue(
                line.account_id, f"Invoice repartition line should have account: {line}"
            )

    def test_06_price_subtotal_total_computation(self):
        """
        Test that price_subtotal and price_total are computed correctly.

        These fields should reflect Brazilian fiscal amounts:
        - price_subtotal: total without taxes (fiscal_amount_untaxed)
        - price_total: total with taxes (fiscal_amount_tax + fiscal_amount_untaxed)
        """
        # Create invoice
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "fiscal_operation_id": self.fo_venda.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "fiscal_operation_id": self.fo_venda.id,
                            "fiscal_operation_line_id": self.fo_venda.line_ids[0].id,
                        }
                    )
                ],
            }
        )

        product_line = invoice.invoice_line_ids[0]

        _logger.info(f"Price unit: {product_line.price_unit}")
        _logger.info(f"Price subtotal: {product_line.price_subtotal}")
        _logger.info(f"Price total: {product_line.price_total}")
        _logger.info(f"Fiscal amount untaxed: {product_line.fiscal_amount_untaxed}")
        _logger.info(f"Fiscal amount tax: {product_line.fiscal_amount_tax}")

        # Verify consistency
        self.assertEqual(
            product_line.price_subtotal,
            product_line.fiscal_amount_untaxed,
            "price_subtotal should match fiscal_amount_untaxed",
        )


@tagged("post_install", "-at_install")
class TestTaxComputationEdgeCases(TransactionCase):
    """
    Test edge cases and error conditions for tax computation.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.env.user.company_id = cls.company
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        cls.product = cls.env.ref("l10n_br_fiscal.customized_development_sale")
        cls.fo_venda = cls.env.ref("l10n_br_fiscal.fo_venda")

    def test_01_invoice_without_fiscal_operation(self):
        """
        Test that non-Brazilian invoices (without fiscal_operation_id)
        still work correctly with standard Odoo tax computation.
        """
        # Create invoice without fiscal operation
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                # No fiscal_operation_id
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            # No fiscal_operation_id on line
                        }
                    )
                ],
            }
        )

        # Should still balance
        total_debit = sum(invoice.line_ids.mapped("debit"))
        total_credit = sum(invoice.line_ids.mapped("credit"))
        self.assertEqual(
            total_debit, total_credit, "Non-fiscal invoice should still balance"
        )

    def test_02_empty_fiscal_taxes(self):
        """
        Test compute_all behavior when fiscal_taxes parameter is empty.
        """
        account_tax = self.env["account.tax"].search(
            [
                ("company_id", "=", self.company.id),
            ],
            limit=1,
        )

        # Call with empty fiscal_taxes
        result = account_tax.compute_all(
            price_unit=100.0,
            currency=self.company.currency_id,
            quantity=1.0,
            fiscal_taxes=self.env["l10n_br_fiscal.tax"],  # Empty recordset
        )

        # Should still return valid result
        self.assertIn("total_excluded", result)
        self.assertIn("total_included", result)

    def test_03_multiple_tax_lines(self):
        """
        Test that multiple taxes (ICMS, IPI, PIS, COFINS) create correct tax lines.
        """
        # Create invoice
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "fiscal_operation_id": self.fo_venda.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": 1000.0,  # Higher amount to see multiple taxes
                            "fiscal_operation_id": self.fo_venda.id,
                            "fiscal_operation_line_id": self.fo_venda.line_ids[0].id,
                        }
                    )
                ],
            }
        )

        tax_lines = invoice.line_ids.filtered(lambda line: line.display_type == "tax")
        _logger.info(f"Number of tax lines: {len(tax_lines)}")

        for line in tax_lines:
            _logger.info(
                f"Tax line: {line.name}, debit={line.debit}, credit={line.credit}"
            )

        # Verify entry balances
        total_debit = sum(invoice.line_ids.mapped("debit"))
        total_credit = sum(invoice.line_ids.mapped("credit"))
        self.assertEqual(
            total_debit, total_credit, "Entry with multiple taxes should balance"
        )


@tagged("post_install", "-at_install")
class TestTaxDataStructure(TransactionCase):
    """
    Document the data structures used in tax computation for v18 reference.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.env.user.company_id = cls.company

    def test_01_compute_all_return_structure(self):
        """
        Document the exact structure returned by compute_all.

        This is important for v18 refactoring where we need to produce
        compatible data structures.
        """
        tax = self.env["account.tax"].search(
            [
                ("company_id", "=", self.company.id),
            ],
            limit=1,
        )

        result = tax.compute_all(100.0, self.company.currency_id, 1.0)

        # Document the structure
        _logger.info("=" * 60)
        _logger.info("compute_all return structure:")
        _logger.info("=" * 60)
        for key, value in result.items():
            _logger.info(f"  {key}: {type(value)} = {value}")

        # Verify expected keys exist
        expected_keys = ["total_excluded", "total_included", "taxes", "base_tags"]
        for key in expected_keys:
            self.assertIn(key, result, f"Missing key: {key}")

        # Document tax structure
        if result["taxes"]:
            _logger.info("\nTax structure (first tax):")
            first_tax = result["taxes"][0]
            for key, value in first_tax.items():
                _logger.info(f"  {key}: {type(value)} = {value}")

    def test_02_compute_all_tax_field_structure(self):
        """
        Document the compute_all_tax field structure.

        This field contains the computed tax data that drives tax line creation.
        """
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                "company_id": self.company.id,
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.env.ref(
                                "l10n_br_fiscal.customized_development_sale"
                            ).id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "fiscal_operation_id": self.env.ref(
                                "l10n_br_fiscal.fo_venda"
                            ).id,
                            "fiscal_operation_line_id": self.env.ref(
                                "l10n_br_fiscal.fo_venda"
                            )
                            .line_ids[0]
                            .id,
                        }
                    )
                ],
            }
        )

        line = invoice.invoice_line_ids[0]
        line._compute_all_tax()

        _logger.info("=" * 60)
        _logger.info("compute_all_tax field structure:")
        _logger.info("=" * 60)
        _logger.info(f"Type: {type(line.compute_all_tax)}")

        if line.compute_all_tax:
            for key, value in line.compute_all_tax.items():
                _logger.info(f"\nKey: {key}")
                _logger.info(f"  Type: {type(key)}")
                _logger.info(f"  Value type: {type(value)}")
                if isinstance(value, dict):
                    for k, v in value.items():
                        _logger.info(f"    {k}: {type(v)} = {v}")

    def test_03_tax_repartition_line_structure(self):
        """
        Document the tax repartition line structure.
        """
        tax = self.env["account.tax"].search(
            [
                ("company_id", "=", self.company.id),
                ("name", "like", "ICMS Saída"),
            ],
            limit=1,
        )

        _logger.info("=" * 60)
        _logger.info("Tax repartition line structure:")
        _logger.info("=" * 60)

        for line in tax.invoice_repartition_line_ids:
            _logger.info(f"\nRepartition line: {line.id}")
            _logger.info(f"  repartition_type: {line.repartition_type}")
            _logger.info(f"  factor_percent: {line.factor_percent}")
            _logger.info(f"  account_id: {line.account_id}")
            _logger.info(f"  use_in_tax_closing: {line.use_in_tax_closing}")
