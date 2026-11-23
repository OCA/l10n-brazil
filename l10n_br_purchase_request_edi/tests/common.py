# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, fields

from odoo.addons.l10n_br_purchase_edi.tests.common import PurchaseEdiCase


class RequestEdiCase(PurchaseEdiCase):
    def _request(self, quantity=10.0, estimated=1000.0, approve=True, product=None):
        product = product or self.product
        request = self.env["purchase.request"].create(
            {
                "company_id": self.company.id,
                "requested_by": self.env.user.id,
                "line_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "name": product.name,
                            "product_qty": quantity,
                            "product_uom_id": self.unit.id,
                            "estimated_cost": estimated,
                            "date_required": fields.Date.today(),
                        }
                    )
                ],
            }
        )
        if approve:
            request.button_to_approve()
            request.button_approved()
        return request

    def _note_rows_and_request(self, request):
        rows = self._rows(fiscal_document_id=self.document.id)
        return rows | self._rows(purchase_request_line_id=request.line_ids.id)
