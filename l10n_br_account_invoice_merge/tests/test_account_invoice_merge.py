# Copyright 2023 - Mateus ONunes <mateus.2006@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError

from odoo.addons.account.tests.common import AccountTestInvoicingCommon, tagged


@tagged("post_install", "-at_install")
class TestAccountInvoiceMerge(AccountTestInvoicingCommon):
    """
    Tests for l10n_br Account Invoice Merge.
    """

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref)
        cls.env.user.groups_id |= cls.env.ref("l10n_br_fiscal.group_manager")
        cls.par_model = cls.env["res.partner"]
        cls.context = cls.env["res.users"].context_get()
        cls.acc_model = cls.env["account.account"]
        cls.inv_model = cls.env["account.move"]
        cls.inv_line_model = cls.env["account.move.line"]
        cls.wiz = cls.env["invoice.merge"]
        cls.product = cls.env.ref("product.product_product_8")
        cls.account_receive = cls.env.ref("account.data_account_type_receivable")
        cls.partner1 = cls._create_partner(cls)
        cls.invoice_account = cls.acc_model.search(
            [("user_type_id", "=", cls.account_receive.id)],
            limit=1,
        )
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "sale")], limit=1
        )

        cls.document_type01 = cls.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", "01")], limit=1
        )

        cls.fiscal_operation_venda = cls.env["l10n_br_fiscal.operation"].search(
            [("code", "=", "Venda")], limit=1
        )

        cls.invoice1 = cls._create_invoice(cls, cls.partner1, "A")

    def _create_partner(self):
        partner = self.par_model.create(
            {"name": "Test Partner", "supplier_rank": 1, "company_type": "company"}
        )
        return partner

    def _create_inv_line(self, invoice):
        lines = invoice.invoice_line_ids
        invoice.write(
            {
                "invoice_line_ids": [
                    (
                        0,
                        False,
                        {
                            "name": "test invoice line",
                            "quantity": 1.0,
                            "price_unit": 3.0,
                            "move_id": invoice.id,
                            "product_id": self.product.id,
                            "exclude_from_invoice_tab": False,
                        },
                    )
                ]
            }
        )
        return invoice.invoice_line_ids - lines

    def _create_invoice(self, partner, name, journal=False, move_type=False):
        if not journal:
            journal = self.journal
        if not move_type:
            move_type = "out_invoice"

        invoice = self.inv_model.create(
            {
                "partner_id": partner.id,
                "name": name,
                "move_type": move_type,
                "journal_id": journal.id,
                "document_type_id": self.document_type01.id,
                "fiscal_operation_id": self.fiscal_operation_venda.id,
                "invoice_line_ids": [
                    (
                        0,
                        False,
                        {
                            "name": "test invoice line",
                            "quantity": 1.0,
                            "price_unit": 3.0,
                            "product_id": self.product.id,
                            "exclude_from_invoice_tab": False,
                        },
                    )
                ],
            }
        )
        return invoice

    def test_dirty_check(self):
        """Check l10n_br fields"""
        wiz_id = self.wiz.with_context(active_model="account.move")

        # Check with two different document type
        # Create the invoice 2 with a different document type
        invoice2 = self._create_invoice(self.partner1, "D")
        document_type02 = self.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", "02")], limit=1
        )
        invoice2.write({"document_type_id": document_type02.id})
        invoices = self.invoice1 | invoice2
        with self.assertRaises(UserError):
            wiz_id.with_context(
                active_ids=invoices.ids,
                active_model=invoices._name,
            ).fields_view_get()

        # Check with two different fiscal_operation_id
        # Create the invoice 3 with a different document type
        fiscal_operation_compras = self.env["l10n_br_fiscal.operation"].search(
            [("code", "=", "Compras")], limit=1
        )
        invoice3 = self._create_invoice(self.partner1, "D")
        invoice3.write({"fiscal_operation_id": fiscal_operation_compras.id})
        invoices = self.invoice1 | invoice3
        with self.assertRaises(UserError):
            wiz_id.with_context(
                active_ids=invoices.ids,
                active_model=invoices._name,
            ).fields_view_get()
