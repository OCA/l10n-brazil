from odoo.tests.common import SavepointCase


class TestL10nBrHrExpenseInvoice(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sheet_id = cls.env["hr.expense.sheet"].create(
            {
                "name": "First Expense for employee",
                "employee_id": cls.env.ref("hr.employee_admin").id,
                "company_id": cls.env.ref("base.main_company").id,
                "expense_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "expense_1",
                            "product_id": cls.env.ref("hr_expense.car_travel").id,
                            "product_uom_id": cls.env.ref(
                                "hr_expense.car_travel"
                            ).uom_id.id,
                            "unit_amount": 500.0,
                            "employee_id": cls.env.ref("hr.employee_admin").id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "expense_2",
                            "product_id": cls.env.ref("hr_expense.air_ticket").id,
                            "product_uom_id": cls.env.ref(
                                "hr_expense.air_ticket"
                            ).uom_id.id,
                            "unit_amount": 700.0,
                            "employee_id": cls.env.ref("hr.employee_admin").id,
                            "fiscal_operation_id": cls.env.ref(
                                "l10n_br_fiscal.fo_venda"
                            ).id,
                        },
                    ),
                ],
            }
        )

        cls.sheet_id.action_submit_sheet()
        cls.sheet_id.approve_expense_sheets()

        for expense_line in cls.sheet_id.expense_line_ids:
            expense_line.action_expense_create_invoice()

    def test_created_invoices(self):
        invoices = self.sheet_id.expense_line_ids.mapped("invoice_id")
        self.assertEqual(
            len(invoices), 2, "The number of created invoices is not as expected."
        )
        invoice_1 = self.sheet_id.expense_line_ids.filtered(
            lambda line: line.name == "expense_1"
        ).invoice_id
        invoice_2 = self.sheet_id.expense_line_ids.filtered(
            lambda line: line.name == "expense_2"
        ).invoice_id
        self.assertFalse(
            invoice_1.fiscal_operation_id,
            "Fiscal operation ID should be empty for expense 1.",
        )
        self.assertTrue(
            invoice_2.fiscal_operation_id,
            "Fiscal operation ID should be set for expense 2.",
        )
