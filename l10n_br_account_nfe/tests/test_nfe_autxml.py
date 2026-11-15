# Copyright 2026 Engenere.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestNFeAutXML(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_normal_company_taxes()
        cls.company = cls.company_data["company"]
        cls.other_company = cls.company_data_2["company"]
        cls.accountant = cls.env["res.partner"].create(
            {"name": "Accountant", "is_company": True, "cnpj_cpf": "11.222.333/0001-81"}
        )
        cls.other_accountant = cls.env["res.partner"].create(
            {"name": "Other Company Accountant"}
        )
        for company, accountant in (
            (cls.company, cls.accountant),
            (cls.other_company, cls.other_accountant),
        ):
            company.write(
                {
                    "accountant_id": accountant.id,
                    "nfe_authorize_accountant_download_xml": True,
                }
            )

    def _create_invoice(self, move_model):
        operation = self.env.ref("l10n_br_fiscal.fo_venda")
        return move_model.create(
            {
                "move_type": "out_invoice",
                "company_id": self.company.id,
                "partner_id": self.partner_a.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "document_serie_id": self.empresa_lc_document_55_serie_1.id,
                "fiscal_operation_id": operation.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_b.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                            "fiscal_operation_id": operation.id,
                            "fiscal_operation_line_id": self.env.ref(
                                "l10n_br_fiscal.fo_venda_venda"
                            ).id,
                        }
                    )
                ],
            }
        )

    def test_invoice_authorizes_the_accountant(self):
        """The accountant of the company goes to the autXML of the invoice."""
        invoice = self._create_invoice(
            self.env["account.move"].with_company(self.company)
        )

        autxml = invoice.fiscal_document_id.nfe40_autXML
        self.assertEqual(autxml.partner_id, self.accountant)
        self.assertEqual(autxml.nfe40_CNPJ, "11222333000181")

    def test_invoice_from_another_active_company(self):
        """The autXML comes from the invoice company, not the active one.

        sale.order._create_invoices creates the invoice without switching
        to the order company, so the user may be working on another one.
        """
        move_model = self.env["account.move"].with_context(
            allowed_company_ids=[self.other_company.id, self.company.id]
        )
        self.assertEqual(move_model.env.company, self.other_company)

        invoice = self._create_invoice(move_model)

        self.assertEqual(
            invoice.fiscal_document_id.nfe40_autXML.partner_id, self.accountant
        )

    def test_invoice_autxml_field_points_to_the_concrete_model(self):
        """account.move inherits nfe40_autXML through _inherits.

        Its copy of the field must point to the concrete l10n_br_nfe.autxml
        whatever the module loading order, or creating an invoice fails
        with "Invalid field 'partner_id' on model 'nfe.40.autxml'".
        """
        field = self.env["account.move"]._fields["nfe40_autXML"]
        self.assertEqual(field.comodel_name, "l10n_br_nfe.autxml")
