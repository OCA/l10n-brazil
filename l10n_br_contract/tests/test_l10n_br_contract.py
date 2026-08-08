# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.exceptions import UserError
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

        # Create contract with 3 lines, two resale products and one service
        contract_form = Form(cls.env["contract.contract"])
        contract_form.name = "Test Contract"
        contract_form.line_recurrence = True
        contract_form.partner_id = cls.env.ref("l10n_br_base.res_partner_kmee")

        cls.contract_id = contract_form.save()

        with Form(cls.contract_id) as contract:
            with contract.contract_line_ids.new() as line:
                line.product_id = cls.env.ref("product.product_delivery_01")
            with contract.contract_line_ids.new() as line:
                line.product_id = cls.env.ref("product.product_delivery_02")
            with contract.contract_line_ids.new() as line:
                line.product_id = cls.env.ref(
                    "l10n_br_fiscal.customized_development_sale"
                )
                line.fiscal_operation_id = cls.env.ref("l10n_br_fiscal.fo_venda")
                line.price_unit = 550.00

        # Create Invoice and Fiscal Documents related to the contract
        cls.contract_id.recurring_create_invoice()

    def test_fiscal_fields_loaded_on_product_change(self):
        """Fiscal operation line and ICMS/ISSQN must load like sale/purchase."""
        contract_form = Form(self.env["contract.contract"])
        contract_form.name = "Contract Fiscal Autofill"
        contract_form.line_recurrence = True
        contract_form.partner_id = self.env.ref("l10n_br_base.res_partner_kmee")
        contract_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        contract = contract_form.save()

        product_goods = self.env.ref("product.product_delivery_01")
        product_service = self.env.ref("l10n_br_fiscal.customized_development_sale")

        with Form(contract) as contract_form:
            with contract_form.contract_line_ids.new() as line:
                line.product_id = product_goods
            with contract_form.contract_line_ids.new() as line:
                line.product_id = product_service
                line.price_unit = 100.0

        goods_line = contract.contract_line_ids.filtered(
            lambda ln: ln.product_id == product_goods
        )
        service_line = contract.contract_line_ids.filtered(
            lambda ln: ln.product_id == product_service
        )

        self.assertTrue(goods_line.fiscal_operation_id)
        self.assertTrue(
            goods_line.fiscal_operation_line_id,
            "Fiscal operation line should be computed when product is set",
        )
        self.assertEqual(
            goods_line.tax_icms_or_issqn,
            product_goods.tax_icms_or_issqn or TAX_DOMAIN_ICMS,
        )

        self.assertTrue(service_line.fiscal_operation_id)
        self.assertTrue(
            service_line.fiscal_operation_line_id,
            "Fiscal operation line should be computed for service products",
        )
        self.assertEqual(
            service_line.tax_icms_or_issqn,
            product_service.tax_icms_or_issqn or TAX_DOMAIN_ISSQN,
        )

    def test_get_view_injects_fiscal_fields(self):
        if self.env.company.country_id.code != "BR":
            self.skipTest("Company country is not Brazil")
        arch, _view = self.env["contract.contract"]._get_view(view_type="form")
        arch_str = etree.tostring(arch, encoding="unicode")
        self.assertIn("fiscal_operation_line_id", arch_str)
        self.assertIn("tax_icms_or_issqn", arch_str)

    def test_user_error_missing_fiscal_operation(self):
        contract_form = Form(self.env["contract.contract"])
        contract_form.name = "Contract Without Fiscal Operation Line"
        contract_form.line_recurrence = True
        contract_form.partner_id = self.env.ref("l10n_br_base.res_partner_kmee")
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
                service_product_id = self.env.ref(
                    "l10n_br_fiscal.customized_development_sale"
                )
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
                product_1_id = self.env.ref("product.product_delivery_01")
                product_2_id = self.env.ref("product.product_delivery_02")
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
                service_product_id = self.env.ref(
                    "l10n_br_fiscal.customized_development_sale"
                )

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
                product_1_id = self.env.ref("product.product_delivery_01")
                product_2_id = self.env.ref("product.product_delivery_02")

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
