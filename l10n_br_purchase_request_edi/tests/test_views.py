# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import tagged

from odoo.addons.l10n_br_fiscal_edi.tests.common import EdiImportCase


@tagged("post_install", "-at_install")
class TestViews(EdiImportCase):
    def _check_fields(self, model, node):
        for field in node.iterchildren():
            if field.tag != "field":
                self._check_fields(model, field)
                continue
            name = field.get("name")
            self.assertIn(name, self.env[model]._fields, f"{model}.{name}")
            comodel = self.env[model]._fields[name].comodel_name
            for sub in field.xpath("./tree|./form"):
                self._check_fields(comodel, sub)

    def _buyer(self):
        buyer = self._fiscal_user("view-buyer")
        buyer.groups_id |= self.env.ref("purchase.group_purchase_user")
        return buyer

    def test_every_field_of_the_views_exists_in_the_model(self):
        view_ids = (
            self.env["ir.model.data"]
            .search(
                [
                    ("module", "=", "l10n_br_purchase_request_edi"),
                    ("model", "=", "ir.ui.view"),
                ]
            )
            .mapped("res_id")
        )
        views = self.env["ir.ui.view"].browse(view_ids)
        self.assertTrue(views)
        requester = self._fiscal_user("view-requester")
        requester.groups_id |= self.env.ref(
            "purchase_request.group_purchase_request_manager"
        )
        for user in (self._fiscal_user("view-fiscal"), self._buyer(), requester):
            for view in views.filtered(lambda view: view.type in ("form", "tree")):
                if view.model == "purchase.request" and not user.has_group(
                    "purchase_request.group_purchase_request_user"
                ):
                    continue  # the request form is for the request users
                model = (
                    self.env[view.model]
                    .with_user(user)
                    .with_context(allowed_company_ids=user.company_ids.ids)
                )
                arch = model.get_view(view.id)["arch"]
                self._check_fields(view.model, etree.fromstring(arch))
