# Copyright 2024 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

from ..constants.fiscal import FINAL_CUSTOMER_NO, FINAL_CUSTOMER_YES


class TestOperation(TransactionCase):
    def test_copy(self):
        """Test Operation copy()"""
        operation_venda = self.env.ref("l10n_br_fiscal.fo_venda")
        operation_venda_copy = operation_venda.copy()
        self.assertEqual(operation_venda_copy.name, "Venda")
        self.assertEqual(operation_venda_copy.code, "VD (Copy)")


class TestOperationLineIndFinal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Partner Ind Final"})
        cls.product = cls.env["product.product"].create({"name": "Product Ind Final"})

        cls.operation = cls._create_operation("IND FINAL", "Operation Ind Final")
        cls.line_any = cls._create_line(cls.operation, "Any", False)
        cls.line_final = cls._create_line(cls.operation, "Final", FINAL_CUSTOMER_YES)
        cls.line_resale = cls._create_line(cls.operation, "Resale", FINAL_CUSTOMER_NO)

    @classmethod
    def _create_operation(cls, code, name):
        return cls.env["l10n_br_fiscal.operation"].create(
            {
                "code": code,
                "name": name,
                "fiscal_operation_type": "out",
                "state": "approved",
            }
        )

    @classmethod
    def _create_line(cls, operation, name, ind_final):
        return cls.env["l10n_br_fiscal.operation.line"].create(
            {
                "fiscal_operation_id": operation.id,
                "name": name,
                "ind_final": ind_final,
                "state": "approved",
            }
        )

    def _line_definition(self, operation, ind_final=None):
        return operation.line_definition(
            company=self.env.company,
            partner=self.partner,
            product=self.product,
            ind_final=ind_final,
        )

    def test_line_ind_final_yes(self):
        """A final consumption operation picks the line set to Yes"""
        self.assertEqual(
            self._line_definition(self.operation, FINAL_CUSTOMER_YES),
            self.line_final,
        )

    def test_line_ind_final_no(self):
        """An operation that is not for final consumption picks the line set
        to No, instead of the generic line that comes first"""
        self.assertEqual(
            self._line_definition(self.operation, FINAL_CUSTOMER_NO),
            self.line_resale,
        )

    def test_line_without_ind_final(self):
        """Lines that leave the indicator empty keep matching any operation,
        as they did before the criterion existed"""
        operation = self._create_operation("IND FINAL 2", "Operation Any Ind Final")
        line_any = self._create_line(operation, "Any", False)

        for ind_final in (FINAL_CUSTOMER_YES, FINAL_CUSTOMER_NO, None):
            self.assertEqual(self._line_definition(operation, ind_final), line_any)
