# Copyright 2026 Engenere.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestNFeAutXMLComodel(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_normal_company_taxes()
        cls.accountant = cls.env["res.partner"].create({"name": "Accountant"})
        cls.company_data["company"].write(
            {
                "accountant_id": cls.accountant.id,
                "nfe_authorize_accountant_download_xml": True,
            }
        )

    def test_invoice_autxml_field_points_to_the_concrete_model(self):
        """account.move inherits nfe40_autXML through _inherits.

        Its copy of the field must point to the concrete l10n_br_nfe.autxml
        whatever the module loading order.
        """
        field = self.env["account.move"]._fields["nfe40_autXML"]
        self.assertEqual(field.comodel_name, "l10n_br_nfe.autxml")

    def test_invoice_authorizes_the_accountant(self):
        """Creating an invoice authorizes the accountant of the company.

        The autXML default goes through the copy of the field on
        account.move: pointing to the abstract nfe.40.autxml, creating the
        invoice failed with "Invalid field 'partner_id' on model
        'nfe.40.autxml'".
        """
        invoice = self.init_invoice(
            move_type="out_invoice",
            products=[self.product_b],
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=self.empresa_lc_document_55_serie_1,
            fiscal_operation=self.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[self.env.ref("l10n_br_fiscal.fo_venda_venda")],
        )

        self.assertEqual(invoice.nfe40_autXML.partner_id, self.accountant)
