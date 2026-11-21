# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta

from odoo.tests import TransactionCase


class TestL10nBrProductContract(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.company.create_contract_at_sale_order_confirmation = True
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.fiscal_operation_line = cls.env.ref("l10n_br_fiscal.fo_venda_servico")
        cls.contract_template = cls.env["contract.template"].create(
            {
                "name": "Test - Sale Contract Template",
                "contract_type": "sale",
                "company_id": cls.company.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test - Recurrency Service",
                "type": "service",
                "list_price": 100.0,
                "default_code": "RECURRENCY_TEST",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "ncm_id": cls.env.ref("l10n_br_fiscal.ncm_00000000").id,
                "fiscal_type": "09",
                "tax_icms_or_issqn": "issqn",
                "fiscal_genre_id": cls.env.ref("l10n_br_fiscal.product_genre_00").id,
                "service_type_id": cls.env.ref("l10n_br_fiscal.service_type_105").id,
                "is_contract": True,
                # The recurrence is defined on the product: the contract line
                # end date is computed from it when the sale line is created.
                "recurrence_number": 12,
                "recurrence_interval": "monthly",
                "recurring_rule_type": "monthly",
                "recurring_interval": 1,
                "recurring_invoicing_type": "pre-paid",
                "property_contract_template_id": cls.contract_template.id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test - Contract Customer",
                "company_type": "company",
                "country_id": cls.env.ref("base.br").id,
            }
        )

    def _create_sale_order(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "fiscal_operation_id": self.fiscal_operation.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Recurring service",
                            "product_id": self.product.id,
                            "product_uom_qty": 2,
                            "price_unit": 500,
                            "fiscal_operation_id": self.fiscal_operation.id,
                            "fiscal_operation_line_id": self.fiscal_operation_line.id,
                        },
                    )
                ],
            }
        )
        return order

    def test_confirm_sale_order_creates_contract_with_fiscal_operation(self):
        order = self._create_sale_order()
        order.action_confirm()
        sale_line = order.order_line
        contract = sale_line.contract_id
        self.assertTrue(contract)
        # Header: the fiscal operation of the order goes to the contract
        self.assertEqual(contract.fiscal_operation_id, self.fiscal_operation)
        # Line: the fiscal operation, its line and the taxes go to the contract line
        contract_line = contract.contract_line_ids
        self.assertEqual(len(contract_line), 1)
        self.assertEqual(contract_line.fiscal_operation_id, self.fiscal_operation)
        self.assertEqual(
            contract_line.fiscal_operation_line_id, self.fiscal_operation_line
        )
        self.assertEqual(contract_line.cfop_id, sale_line.cfop_id)
        self.assertEqual(contract_line.fiscal_tax_ids, sale_line.fiscal_tax_ids)
        self.assertEqual(contract_line.quantity, 2)
        self.assertEqual(contract_line.price_unit, 500)
        # 12 monthly periods: more than one invoice can be generated
        self.assertEqual(
            contract_line.date_end,
            contract_line.date_start + relativedelta(months=12) - relativedelta(days=1),
        )

    def test_contract_invoice_keeps_fiscal_operation_and_taxes(self):
        order = self._create_sale_order()
        order.action_confirm()
        sale_line = order.order_line
        invoice = sale_line.contract_id.recurring_create_invoice()
        self.assertEqual(len(invoice), 1)
        fiscal_document = invoice.fiscal_document_id
        self.assertEqual(fiscal_document.fiscal_operation_id, self.fiscal_operation)
        self.assertEqual(
            fiscal_document.document_type_id,
            self.fiscal_operation_line.get_document_type(self.company),
        )
        fiscal_line = fiscal_document.fiscal_line_ids
        self.assertEqual(len(fiscal_line), 1)
        self.assertEqual(
            fiscal_line.fiscal_operation_line_id, self.fiscal_operation_line
        )
        self.assertEqual(fiscal_line.cfop_id, sale_line.cfop_id)
        self.assertEqual(fiscal_line.fiscal_tax_ids, sale_line.fiscal_tax_ids)
        self.assertEqual(fiscal_line.issqn_value, sale_line.issqn_value)
        self.assertEqual(fiscal_line.amount_fiscal, 1000)
