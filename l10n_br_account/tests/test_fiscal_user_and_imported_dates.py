# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import Command
from odoo.tests import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestFiscalUserAndImportedDates(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        # with l10n_br_account_nfe installed, the NF-e tags of a document are read
        # by whoever works on it, and the NF-e models have rights for this group
        nfe_group = cls.env.ref("l10n_br_nfe.group_manager", False)
        if nfe_group:
            cls.env.user.groups_id |= nfe_group
        cls.company = cls.env.company
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.product = cls.env["product.product"].create(
            {"name": "Imported service", "type": "service"}
        )
        user_groups = [
            cls.env.ref("base.group_user").id,
            cls.env.ref("l10n_br_fiscal.group_user").id,
        ]
        if nfe_group:
            user_groups.append(nfe_group.id)
        cls.fiscal_user = cls.env["res.users"].create(
            {
                "name": "Fiscal without accounting",
                "email": "fiscal-no-accounting@example.com",
                "login": "fiscal_no_accounting",
                "company_id": cls.company.id,
                "company_ids": [Command.set(cls.company.ids)],
                "groups_id": [Command.set(user_groups)],
            }
        )

    def _reload(self):
        """What the web client does not have in memory is read again, as the user."""
        self.env.flush_all()
        self.env.invalidate_all()

    def _can_read_field(self, record, name):
        comodel = record._fields[name].comodel_name
        if not comodel:
            return True
        return record.env[comodel].check_access_rights("read", raise_exception=False)

    def _imported_document(self, **values):
        vals = {
            "company_id": self.company.id,
            "document_type_id": self.env.ref("l10n_br_fiscal.document_SE").id,
            "document_serie": "1",
            "document_number": "100",
            "issuer": "partner",
            "partner_id": self.partner_a.id,
            "fiscal_operation_id": self.operation.id,
            "fiscal_operation_type": "in",
            "document_date": "2026-01-10 15:30:00",
            "imported_document": True,
            "fiscal_line_ids": [
                Command.create(
                    {
                        "name": "Imported line",
                        "product_id": self.product.id,
                        "uom_id": self.product.uom_id.id,
                        "quantity": 1,
                        "price_unit": 1000.0,
                        "fiscal_operation_type": "in",
                        "fiscal_operation_id": self.operation.id,
                        "fiscal_operation_line_id": self.env.ref(
                            "l10n_br_fiscal.fo_compras_compras"
                        ).id,
                    }
                )
            ],
        }
        vals.update(values)
        return self.env["l10n_br_fiscal.document"].create(vals)

    def test_a_fiscal_user_without_accounting_opens_the_document(self):
        document = self._imported_document().with_user(self.fiscal_user)
        self._reload()

        arch = etree.fromstring(document.get_view(view_type="form")["arch"])
        # other modules put their own fields in the form (the NF-e volumes of
        # l10n_br_delivery_nfe belong to the stock users); what they need is not what
        # this test proves, so only the fields the fiscal user can read are read
        names = [
            node.get("name")
            for node in arch.xpath("//form//field")
            if node.get("name") in document._fields
            and self._can_read_field(document, node.get("name"))
        ]
        values = document.read(names)[0]

        self.assertEqual(values["document_number"], "100")
        self.assertFalse(arch.xpath("//button[@name='action_view_invoice']"))
        self.assertNotIn("move_count", names)

    def test_a_fiscal_user_without_accounting_confirms_the_document(self):
        document = self._imported_document().with_user(self.fiscal_user)
        self._reload()

        document.action_document_confirm()

        self.assertEqual(document.state_edoc, "autorizada")

    def test_a_fiscal_user_without_accounting_confirms_a_document_of_the_company(self):
        document_type = self.env.ref("l10n_br_fiscal.document_SE")
        serie = self.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "001",
                "name": "Series 1",
                "document_type_id": document_type.id,
                "company_id": self.company.id,
            }
        )
        document = self._imported_document(
            issuer="company",
            imported_document=False,
            document_serie_id=serie.id,
            document_number=False,
            fiscal_operation_type="out",
            fiscal_operation_id=self.env.ref("l10n_br_fiscal.fo_venda").id,
        ).with_user(self.fiscal_user)
        self._reload()

        document.action_document_confirm()

        self.assertEqual(document.state_edoc, "a_enviar")

    def test_a_fiscal_user_without_accounting_works_on_the_document(self):
        document = self._imported_document().with_user(self.fiscal_user)
        self._reload()

        # the onchanges of the form, the counter and the incoterm, the check and the
        # cleaning of the invoices when the document is cancelled or reopened
        document._inverse_company_id()
        document._inverse_partner_id()
        document._inverse_partner_shipping_id()
        document._inverse_user_id()
        self.assertEqual(document.move_count, 0)
        self.assertFalse(document.incoterm_id)
        document._check_cancel_move_ids_allowed()
        document.cancel_move_ids()
        document.action_document_back2draft()

    def test_the_invoice_of_the_accountant_is_posted_with_the_document(self):
        document = self._imported_document()
        move = self.env["account.move"].browse(
            self.env["account.move"].import_fiscal_document(document).id
        )

        document.action_document_confirm()

        self.assertEqual(move.state, "posted")

    def test_the_dates_of_the_file_survive_the_invoice(self):
        document = self._imported_document(date_in_out="2026-01-11 09:45:00")
        issued = document.document_date
        entered = document.date_in_out

        self.env["account.move"].import_fiscal_document(document)

        self.assertEqual(document.document_date, issued)
        self.assertEqual(document.date_in_out, entered)

    def test_without_a_date_of_entry_the_invoice_does_not_make_one(self):
        document = self._imported_document()
        self.assertFalse(document.date_in_out)

        self.env["account.move"].import_fiscal_document(document)

        self.assertFalse(document.date_in_out)
