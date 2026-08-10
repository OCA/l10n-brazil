# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from contextlib import contextmanager

from lxml import etree

from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import Form, TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ISSQN,
)


@tagged("post_install", "-at_install")
class TestL10nBrContract(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.company
        cls.partner = cls.env.ref("l10n_br_base.res_partner_kmee")
        cls.fo_venda = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.fo_compras = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.product_goods = cls.env.ref("product.product_delivery_01")
        cls.product_goods_2 = cls.env.ref("product.product_delivery_02")
        cls.product_service = cls.env.ref("l10n_br_fiscal.customized_development_sale")

        # Create contract with 3 lines, two resale products and one service
        contract_form = Form(cls.env["contract.contract"])
        contract_form.name = "Test Contract"
        contract_form.line_recurrence = True
        contract_form.partner_id = cls.partner

        cls.contract_id = contract_form.save()

        with Form(cls.contract_id) as contract:
            with contract.contract_line_ids.new() as line:
                line.product_id = cls.product_goods
            with contract.contract_line_ids.new() as line:
                line.product_id = cls.product_goods_2
            with contract.contract_line_ids.new() as line:
                line.product_id = cls.product_service
                line.fiscal_operation_id = cls.fo_venda
                line.price_unit = 550.00

        # Create Invoice and Fiscal Documents related to the contract
        cls.contract_id.recurring_create_invoice()

    @contextmanager
    def _temporary_company_country(self, country):
        original_country = self.company.country_id
        self.company.country_id = country
        try:
            yield
        finally:
            self.company.country_id = original_country

    def _create_contract_with_line(
        self, product, price_unit=None, line_recurrence=True, fiscal_operation=None
    ):
        contract_form = Form(self.env["contract.contract"])
        contract_form.name = "Coverage Contract"
        contract_form.line_recurrence = line_recurrence
        contract_form.partner_id = self.partner
        if fiscal_operation:
            contract_form.fiscal_operation_id = fiscal_operation
        if not line_recurrence:
            # Required on contract header when recurrence is not per-line
            contract_form.recurring_interval = 1
            contract_form.recurring_rule_type = "monthly"
            contract_form.recurring_invoicing_type = "pre-paid"
            contract_form.date_start = "2024-01-01"
        contract = contract_form.save()

        line_field = (
            "contract_line_ids" if line_recurrence else "contract_line_fixed_ids"
        )
        with Form(contract) as contract_form:
            with getattr(contract_form, line_field).new() as line:
                line.product_id = product
                if price_unit is not None:
                    line.price_unit = price_unit
        return contract

    def test_fiscal_fields_loaded_on_product_change(self):
        """Fiscal operation line and ICMS/ISSQN must load like sale/purchase."""
        contract = self._create_contract_with_line(
            self.product_goods, fiscal_operation=self.fo_venda
        )
        with Form(contract) as contract_form:
            with contract_form.contract_line_ids.new() as line:
                line.product_id = self.product_service
                line.price_unit = 100.0

        goods_line = contract.contract_line_ids.filtered(
            lambda ln: ln.product_id == self.product_goods
        )
        service_line = contract.contract_line_ids.filtered(
            lambda ln: ln.product_id == self.product_service
        )

        self.assertTrue(goods_line.fiscal_operation_id)
        self.assertTrue(
            goods_line.fiscal_operation_line_id,
            "Fiscal operation line should be computed when product is set",
        )
        self.assertEqual(
            goods_line.tax_icms_or_issqn,
            self.product_goods.tax_icms_or_issqn or TAX_DOMAIN_ICMS,
        )
        self.assertEqual(goods_line.partner_id, contract.partner_id)
        self.assertEqual(goods_line._get_document(), contract)

        self.assertTrue(service_line.fiscal_operation_id)
        self.assertTrue(
            service_line.fiscal_operation_line_id,
            "Fiscal operation line should be computed for service products",
        )
        self.assertEqual(
            service_line.tax_icms_or_issqn,
            self.product_service.tax_icms_or_issqn or TAX_DOMAIN_ISSQN,
        )

    def test_fiscal_fields_loaded_on_fixed_lines(self):
        """Fixed contract lines must also auto-fill fiscal fields."""
        contract = self._create_contract_with_line(
            self.product_goods,
            line_recurrence=False,
            fiscal_operation=self.fo_venda,
        )
        line = contract.contract_line_fixed_ids
        self.assertTrue(line.fiscal_operation_id)
        self.assertTrue(
            line.fiscal_operation_line_id,
            "Fiscal operation line should be computed on fixed lines",
        )
        self.assertEqual(
            line.tax_icms_or_issqn,
            self.product_goods.tax_icms_or_issqn or TAX_DOMAIN_ICMS,
        )

    def test_get_view(self):
        """Cover all _get_view branches for contract.contract."""
        contract_model = self.env["contract.contract"]

        with self.subTest("BR company - form view injects fiscal fields"):
            arch, _view = contract_model._get_view(view_type="form")
            arch_str = etree.tostring(arch, encoding="unicode")
            self.assertIn("fiscal_operation_line_id", arch_str)
            self.assertIn("tax_icms_or_issqn", arch_str)
            self.assertTrue(
                arch.xpath(".//field[@name='icms_tax_id']"),
                "icms_tax_id should be injected for BR company form",
            )

        with self.subTest("Non-BR company - form view skips inject"):
            us_country = self.env.ref("base.us")
            with self._temporary_company_country(us_country):
                arch_non_br, _view = contract_model._get_view(view_type="form")
                self.assertFalse(
                    arch_non_br.xpath(".//field[@name='icms_tax_id']"),
                    "icms_tax_id should not be injected for non-BR company",
                )

        with self.subTest("BR company - tree view is not injected"):
            arch_tree, _view = contract_model._get_view(view_type="tree")
            self.assertFalse(
                arch_tree.xpath(".//field[@name='icms_tax_id']"),
                "Tree view should not run inject_fiscal_fields",
            )

    def test_setup_complete_disables_precompute(self):
        """Mixin fiscal computes must not use precompute on contract.line."""
        line_model = self.env["contract.line"]
        mixin = self.env["l10n_br_fiscal.document.line.mixin"]
        disabled_computes = {
            "_compute_price_unit_fiscal",
            "_compute_product_fiscal_fields",
            "_compute_fiscal_quantity",
            "_compute_fiscal_price",
            "_compute_fiscal_tax_ids",
            "_compute_tax_fields",
            "_compute_fiscal_operation_line_id",
            "_compute_comment_ids",
        }
        checked = 0
        for name, field in line_model._fields.items():
            mixin_field = mixin._fields.get(name)
            if not mixin_field or mixin_field.compute not in disabled_computes:
                continue
            if getattr(mixin_field, "precompute", False):
                self.assertFalse(
                    getattr(field, "precompute", False),
                    f"Field {name} should have precompute disabled on contract.line",
                )
                checked += 1
        self.assertGreater(
            checked,
            0,
            "Expected at least one mixin precompute field to be disabled",
        )

    def test_default_get_fiscal_operation(self):
        """default_get must set fiscal operation from company defaults."""
        company = self.company
        company.contract_sale_fiscal_operation_id = self.fo_venda
        company.contract_purchase_fiscal_operation_id = self.fo_compras
        contract_model = self.env["contract.contract"]

        sale_defaults = contract_model.with_context(
            default_contract_type="sale",
            default_company_id=company.id,
        ).default_get(["contract_type", "company_id", "fiscal_operation_id"])
        self.assertEqual(sale_defaults.get("fiscal_operation_id"), self.fo_venda.id)

        purchase_defaults = contract_model.with_context(
            default_contract_type="purchase",
        ).default_get(["contract_type", "fiscal_operation_id"])
        self.assertEqual(
            purchase_defaults.get("fiscal_operation_id"), self.fo_compras.id
        )

        sale_form = Form(contract_model.with_context(default_contract_type="sale"))
        self.assertEqual(sale_form.fiscal_operation_id, self.fo_venda)

        purchase_form = Form(
            contract_model.with_context(default_contract_type="purchase")
        )
        self.assertEqual(purchase_form.fiscal_operation_id, self.fo_compras)

    def test_prepare_invoice_line_includes_fiscal_and_currency(self):
        """Invoice line vals must include fiscal dict and company currency."""
        line = self.contract_id.contract_line_ids[:1]
        invoice_line_vals = line._prepare_invoice_line()
        self.assertEqual(
            invoice_line_vals.get("company_currency_id"),
            self.contract_id.company_id.currency_id.id,
        )
        self.assertTrue(
            invoice_line_vals.get("fiscal_operation_id")
            or invoice_line_vals.get("fiscal_operation_line_id")
            or line.fiscal_operation_id,
            "Fiscal data should be prepared for invoice lines",
        )
        self.assertIn("tax_ids", invoice_line_vals)
        self.assertIn("quantity", invoice_line_vals)

    def test_prepare_recurring_invoices_without_contract_fiscal_operation(self):
        """Without contract fiscal operation, document_type_id must be cleared."""
        contract = self._create_contract_with_line(
            self.product_goods, price_unit=10.0, fiscal_operation=self.fo_venda
        )
        contract.fiscal_operation_id = False
        inv_vals = contract._prepare_recurring_invoices_values()
        if not isinstance(inv_vals, list):
            inv_vals = [inv_vals]
        self.assertTrue(inv_vals, "Expected invoice values to be prepared")
        for inv_val in inv_vals:
            self.assertFalse(
                inv_val.get("document_type_id"),
                "document_type_id must be False when contract has no fiscal operation",
            )

    def test_prepare_invoice_includes_fiscal_dict(self):
        """Contract _prepare_invoice must merge Brazilian fiscal header values."""
        date_invoice = (
            self.contract_id.recurring_next_date
            or self.contract_id.contract_line_ids[:1].recurring_next_date
        )
        fiscal_vals = self.contract_id._prepare_br_fiscal_dict()
        invoice_vals = self.contract_id._prepare_invoice(date_invoice)
        self.assertIn("fiscal_operation_id", invoice_vals)
        for key, value in fiscal_vals.items():
            self.assertEqual(
                invoice_vals.get(key),
                value,
                f"Invoice vals missing fiscal key {key} from _prepare_br_fiscal_dict",
            )

    def test_get_fiscal_lines_field_name(self):
        self.assertEqual(
            self.env["contract.contract"]._get_fiscal_lines_field_name(),
            "contract_line_ids",
        )

    def test_withholding_tax_keeps_fiscal_totals(self):
        """Adding a withholding tax must keep totals after form save.

        The line form onchange computes amount_tax_withholding correctly, but
        saving sends fiscal_tax_ids together with *_tax_id. That write used to
        recompute taxes on stale values and persist withholding=0.
        """
        contract = self._create_contract_with_line(
            self.product_service,
            price_unit=100.0,
            fiscal_operation=self.fo_venda,
        )
        line = contract.contract_line_ids
        line.write({"quantity": 1.0, "price_unit": 100.0})

        inss_wh = self.env["l10n_br_fiscal.tax"].search(
            [("tax_domain", "=", "inss_wh")], limit=1
        )
        if not inss_wh:
            self.skipTest("No inss_wh fiscal tax found in demo data.")

        # Reproduce UI save: both fiscal_tax_ids and the specific tax field.
        taxes = line.fiscal_tax_ids | inss_wh
        line.write(
            {
                "inss_wh_tax_id": inss_wh.id,
                "fiscal_tax_ids": [Command.set(taxes.ids)],
            }
        )
        line.invalidate_recordset()

        self.assertAlmostEqual(line.price_gross, 100.0, places=2)
        self.assertTrue(
            line.amount_tax_withholding,
            "amount_tax_withholding must persist after saving fiscal taxes.",
        )
        self.assertAlmostEqual(
            line.fiscal_amount_total,
            line.fiscal_amount_untaxed
            + line.fiscal_amount_tax
            - line.amount_tax_withholding,
            places=2,
        )

    def test_withholding_tax_persists_on_create(self):
        """Creating a line with fiscal_tax_ids + *_tax_id must keep withholding."""
        inss_wh = self.env["l10n_br_fiscal.tax"].search(
            [("tax_domain", "=", "inss_wh")], limit=1
        )
        if not inss_wh:
            self.skipTest("No inss_wh fiscal tax found in demo data.")

        contract = self._create_contract_with_line(
            self.product_service,
            price_unit=100.0,
            fiscal_operation=self.fo_venda,
        )
        template = contract.contract_line_ids
        taxes = template.fiscal_tax_ids | inss_wh

        line = self.env["contract.line"].create(
            {
                "contract_id": contract.id,
                "product_id": self.product_service.id,
                "name": self.product_service.display_name,
                "quantity": 1.0,
                "price_unit": 100.0,
                "uom_id": self.product_service.uom_id.id,
                "date_start": "2024-01-01",
                "recurring_next_date": "2024-01-01",
                "fiscal_operation_id": self.fo_venda.id,
                "fiscal_operation_line_id": template.fiscal_operation_line_id.id,
                "fiscal_tax_ids": [Command.set(taxes.ids)],
                "inss_wh_tax_id": inss_wh.id,
            }
        )
        line.invalidate_recordset()

        self.assertAlmostEqual(line.price_gross, 100.0, places=2)
        self.assertTrue(
            line.amount_tax_withholding,
            "amount_tax_withholding must persist after create with fiscal taxes.",
        )
        self.assertAlmostEqual(
            line.fiscal_amount_total,
            line.fiscal_amount_untaxed
            + line.fiscal_amount_tax
            - line.amount_tax_withholding,
            places=2,
        )

    def test_user_error_missing_fiscal_operation(self):
        contract_form = Form(self.env["contract.contract"])
        contract_form.name = "Contract Without Fiscal Operation Line"
        contract_form.line_recurrence = True
        contract_form.partner_id = self.partner
        contract = contract_form.save()

        with Form(contract) as contract_form:
            with contract_form.contract_line_ids.new() as line:
                line.product_id = self.env.ref("product.expense_product")

        with self.assertRaises(UserError):
            contract.recurring_create_invoice()

    def test_created_fiscal_documents(self):
        """
        Checks if the Fiscal Documents created from a contract have the correct
        products according to the Fiscal Operation of their lines
        """
        for invoice in self.contract_id._get_related_invoices():
            document_id = invoice.fiscal_document_id

            if len(document_id.fiscal_line_ids) == 1:
                service_product_id = self.product_service
                document_type_id = self.env.ref("l10n_br_fiscal.document_SE")

                self.assertEqual(
                    document_type_id.id,
                    document_id.document_type_id.id,
                    "The Fiscal Document Type is not Nota Fiscal "
                    "de Serviço Eletrônica",
                )

                self.assertEqual(
                    service_product_id.id,
                    document_id.fiscal_line_ids[0].product_id.id,
                    "The product of the Fiscal Document does not "
                    "correspond with the expected",
                )
                self.assertEqual(
                    550.00,
                    document_id.fiscal_line_ids[0].price_unit,
                    "The price unit of the Fiscal Document does not "
                    "correspond with the expected",
                )

            else:
                product_1_id = self.product_goods
                product_2_id = self.product_goods_2
                document_type_id = self.env.ref("l10n_br_fiscal.document_55")

                products_ids = []
                for line in document_id.fiscal_line_ids:
                    products_ids.append(line.product_id.id)

                self.assertEqual(
                    document_type_id.id,
                    document_id.document_type_id.id,
                    "The Fiscal Document Type is not Nota Fiscal " "Eletrônica",
                )

                self.assertEqual(
                    [product_1_id.id, product_2_id.id],
                    products_ids,
                    "The products of the Fiscal Document does not"
                    " correspond with the expected",
                )

    def test_created_invoices(self):
        """
        Checks if invoices created from a contract have the correct products
        according to the Fiscal Operation of their lines
        """
        for invoice in self.contract_id._get_related_invoices():
            if len(invoice.invoice_line_ids) == 1:
                service_product_id = self.product_service

                self.assertEqual(
                    service_product_id.id,
                    invoice.invoice_line_ids[0].product_id.id,
                    "The product of the Fiscal Document does not "
                    "correspond with the expected",
                )

                self.assertEqual(
                    550.00,
                    invoice.invoice_line_ids[0].price_unit,
                    "The price unit of the Invoice does not "
                    "correspond with the expected",
                )

            else:
                product_1_id = self.product_goods
                product_2_id = self.product_goods_2

                products_ids = []
                for line in invoice.invoice_line_ids:
                    products_ids.append(line.product_id.id)

                products_ids.sort()

                self.assertEqual(
                    [product_1_id.id, product_2_id.id],
                    products_ids,
                    "The products of the Fiscal Document does not"
                    " correspond with the expected",
                )
