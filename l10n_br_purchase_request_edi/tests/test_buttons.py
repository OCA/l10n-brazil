# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import tagged

from odoo.addons.l10n_br_fiscal_edi.tests.common import readable_field_names

from .common import RequestEdiCase


@tagged("post_install", "-at_install")
class TestSmartButtons(RequestEdiCase):
    """The document and the purchase request point to each other."""

    def _requester(self):
        user = self._fiscal_user("button-requester")
        # the manager reads the requests of everybody
        user.groups_id |= self.env.ref(
            "purchase_request.group_purchase_request_manager"
        )
        return user

    def _as(self, record, user):
        return record.with_user(user).with_context(
            allowed_company_ids=user.company_ids.ids
        )

    def _arch(self, record, user):
        return etree.fromstring(
            self._as(record, user).get_view(view_type="form")["arch"]
        )

    def _read_form(self, record, arch):
        names = readable_field_names(
            record, [node.get("name") for node in arch.iter("field")]
        )
        record.read(names)

    def _fresh(self):
        self.env.flush_all()
        self.env.invalidate_all()

    def _from_request(self):
        request = self._request()
        self.line.write({"quantity": 4, "price_unit": 125.0, "uom_id": self.unit.id})
        self._resolve_product()
        rows = self._note_rows_and_request(request)
        action = rows.action_create_order_from_request()
        return request, self.env["purchase.order"].browse(action["res_id"])

    def test_the_document_counts_and_opens_the_request_of_its_order(self):
        request, _order = self._from_request()
        self._fresh()

        document = self._as(self.document, self._requester())

        self.assertEqual(document.import_request_count, 1)
        self.assertEqual(document.import_request_ids, request)
        action = document.action_view_import_requests()
        self.assertEqual(action["res_model"], "purchase.request")
        self.assertEqual(action["res_id"], request.id)

    def test_the_request_of_the_order_line_counts_for_a_suggested_origin(self):
        # the order was bought for the request elsewhere, and the line only
        # has it as a suggestion
        request = self._request()
        order = self._order(confirm=False)
        order.order_line.purchase_request_lines = [(6, 0, request.line_ids.ids)]
        order.button_confirm()
        self._resolve_product()
        self.assertEqual(self.line.import_origin_state, "suggested")
        self._fresh()

        document = self._as(self.document, self._requester())

        self.assertEqual(document.import_request_ids, request)

    def test_a_document_without_request_has_none(self):
        self._request()
        self._resolve_product()
        self._fresh()

        document = self._as(self.document, self._requester())

        self.assertEqual(document.import_request_count, 0)

    def test_the_document_opens_the_list_for_several_requests(self):
        first = self._request()
        second = self._request()
        other = self.line.copy({"document_id": self.document.id})
        self._resolve_product()
        self._resolve_product(other)
        for line, request in ((self.line, first), (other, second)):
            order = self._order(confirm=False)
            order.order_line.purchase_request_lines = [(6, 0, request.line_ids.ids)]
            order.button_confirm()
            line.import_purchase_line_id = order.order_line
        self._fresh()

        document = self._as(self.document, self._requester())

        self.assertEqual(document.import_request_count, 2)
        action = document.action_view_import_requests()
        self.assertFalse(action.get("res_id"))
        self.assertEqual(sorted(action["domain"][0][2]), sorted((first | second).ids))

    def test_the_request_counts_and_opens_the_documents(self):
        request, _order = self._from_request()
        self._fresh()

        found = self._as(request, self._fiscal_user("button-fiscal-request"))

        self.assertEqual(found.import_document_count, 1)
        action = found.action_view_import_documents()
        self.assertEqual(action["res_model"], "l10n_br_fiscal.document")
        self.assertEqual(action["res_id"], self.document.id)

    def test_the_count_of_a_list_of_requests_is_read_once(self):
        first, _order = self._from_request()
        second = self._request()
        self._fresh()

        requests = (first | second).with_user(self._fiscal_user("button-list-req"))

        self.assertEqual(requests.mapped("import_document_count"), [1, 0])

    def test_the_buttons_follow_the_groups(self):
        request, _order = self._from_request()
        self._fresh()
        fiscal = self._fiscal_user("button-fiscal-view")
        requester = self._requester()
        name = "//button[@name='action_view_import_requests']"

        arch = self._arch(self.document, fiscal)
        self.assertFalse(arch.xpath(name))
        self.assertFalse(arch.xpath("//field[@name='import_request_count']"))
        self._read_form(self._as(self.document, fiscal), arch)
        arch = self._arch(self.document, requester)
        self.assertTrue(arch.xpath(name))
        self._read_form(self._as(self.document, requester), arch)
        # the request shows the documents to the fiscal group only
        request_only = self._fiscal_user("button-request-only")
        request_only.groups_id = [
            (3, self.env.ref("l10n_br_fiscal.group_user").id),
            (4, self.env.ref("purchase_request.group_purchase_request_manager").id),
        ]
        arch = self._arch(request, request_only)
        self.assertFalse(arch.xpath("//button[@name='action_view_import_documents']"))
        self._read_form(self._as(request, request_only), arch)
        arch = self._arch(request, requester)
        self.assertTrue(arch.xpath("//button[@name='action_view_import_documents']"))
        self._read_form(self._as(request, requester), arch)
