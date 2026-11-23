# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_PARTNER,
    DOCUMENT_STATE_DRAFT,
)


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    has_suggested_import_origin = fields.Boolean(
        compute="_compute_has_suggested_import_origin",
        help="Technical: some line of the imported document has an origin "
        "suggestion waiting for confirmation.",
    )

    edi_can_match_orders = fields.Boolean(
        compute="_compute_edi_can_match_orders",
        help="Technical: a purchase document imported from a partner and still in "
        "draft, the only kind that has an origin to choose.",
    )

    @api.depends("imported_document", "state_edoc", "issuer")
    def _compute_edi_can_match_orders(self):
        for document in self:
            document.edi_can_match_orders = bool(
                document.imported_document
                and document.state_edoc == DOCUMENT_STATE_DRAFT
                and document.issuer == DOCUMENT_ISSUER_PARTNER
            )

    @api.depends("imported_document", "fiscal_line_ids.import_origin_state")
    def _compute_has_suggested_import_origin(self):
        for document in self:
            document.has_suggested_import_origin = bool(
                document.imported_document
                and "suggested"
                in document.fiscal_line_ids.mapped("import_origin_state")
            )

    import_purchase_order_ids = fields.Many2many(
        comodel_name="purchase.order",
        compute="_compute_import_purchase_orders",
        string="Purchase Orders",
        groups="purchase.group_purchase_user",
        help="Technical: the purchase orders that the lines of the document "
        "point to, as resolved or as suggested.",
    )
    import_purchase_order_count = fields.Integer(
        compute="_compute_import_purchase_orders",
        string="Purchases",
        groups="purchase.group_purchase_user",
    )

    @api.depends("fiscal_line_ids.import_purchase_line_id")
    def _compute_import_purchase_orders(self):
        # a reading of the link, not of the orders: sudo, and the button is only
        # in the view of the purchase users
        for document in self:
            orders = document.sudo().fiscal_line_ids.import_purchase_line_id.order_id
            document.import_purchase_order_ids = orders
            document.import_purchase_order_count = len(orders)

    def action_view_import_purchase_orders(self):
        """The purchase order of the document, or the list when there are several."""
        self.ensure_one()
        orders = self.sudo().fiscal_line_ids.import_purchase_line_id.order_id
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "purchase.purchase_form_action"
        )
        if len(orders) == 1:
            action["views"] = [(False, "form")]
            action["res_id"] = orders.id
        else:
            action["domain"] = [("id", "in", orders.ids)]
        return action

    def _edi_import_suggest(self):
        result = super()._edi_import_suggest()
        documents = self.filtered("imported_document")
        # the order the file declares is a decision of the supplier: it gives the
        # product of the line
        documents._edi_import_apply_order_reference()
        # the operation was suggested by the base: an origin resolved now takes
        # the destination of its order along
        documents.fiscal_line_ids._suggest_import_origin()
        return result

    def _edi_import_apply_order_reference(self):
        """Resolve the lines whose file declares one confirmed order line (xPed
        and nItemPed) of this supplier and company: the product is the one of the
        order line, and so is the unit when the file declares none that the
        company knows. A unit the file declares and nothing explains leaves the
        line for the review, as before."""
        uom_model = self.env["uom.uom"]
        supplierinfo_model = self.env["product.supplierinfo"].sudo()
        for line in self.fiscal_line_ids.filtered(
            lambda line: line.import_state in (False, "pending", "matched")
        ):
            order_line = line._find_purchase_line_by_declared_item()
            if not order_line:
                continue
            product = order_line.product_id
            if line.product_id and line.product_id != product:
                continue  # another product was already chosen for the line
            declared = uom_model._match_by_fiscal_code(line.partner_uom_code)
            code = line._get_partner_product_code()
            info = code and supplierinfo_model.search(
                [
                    ("partner_id", "=", self.partner_id.id),
                    ("product_code", "=", code),
                    ("company_id", "in", [False, self.company_id.id]),
                    "|",
                    ("product_id", "=", product.id),
                    ("product_tmpl_id", "=", product.product_tmpl_id.id),
                ],
                limit=1,
            )
            learned_uom, learned_factor = (
                line._get_supplierinfo_unit(info) if info else (uom_model, 1.0)
            )
            if declared and learned_uom == declared:
                line._apply_import_depara(
                    product=product, uom=product.uom_po_id, factor=learned_factor
                )
            elif not declared or declared == order_line.product_uom:
                line._apply_import_depara(
                    product=product, uom=order_line.product_uom, factor=1.0
                )
            else:
                # a unit that the order does not explain: the person decides
                line.product_id = product
                line.import_state = "matched"

    def action_confirm_import_origins(self):
        """Confirm, in one step, the origins suggested on the lines."""
        for document in self:
            document.fiscal_line_ids.filtered(
                lambda line: line.import_origin_state == "suggested"
            ).write({"import_origin_state": "resolved"})
        return True

    def _import_undecided_origin_lines(self):
        """Lines whose origin waits for a person: a suggestion, or a pending
        choice with an order line to choose from."""
        self.ensure_one()
        return self.fiscal_line_ids.filtered(
            lambda line: line.import_origin_state == "suggested"
            or (
                line.import_origin_state == "pending"
                and line.import_origin_candidate_ids
            )
        )

    def action_generate_invoice(self):
        self.ensure_one()
        undecided = self._import_undecided_origin_lines()
        if undecided:
            raise UserError(
                _(
                    "%(count)s line(s) have the origin (purchase order line) "
                    "not decided yet. Use Confirm Origins to accept the "
                    "suggestions, or Match with Orders to choose the order line "
                    "of each one or to mark the line as without order. A line whose "
                    "product is only a suggestion and that declares no order in the "
                    "file gets its origin after Confirm Suggestions.",
                    count=len(undecided),
                )
            )
        return super().action_generate_invoice()

    def action_open_origin_match(self):
        """Open the reconciliation of the document with orders and quotations
        of its supplier."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_br_purchase_edi.document_match_action"
        )
        domain = [
            ("company_id", "=", self.company_id.id),
            # a source may have no partner (a purchase request without preferred
            # supplier): it can be the origin of the document of any supplier
            ("partner_id", "in", [self.partner_id.commercial_partner_id.id, False]),
            "|",
            ("fiscal_document_id", "=", self.id),
            ("kind", "!=", "note"),
        ]
        lines = self.fiscal_line_ids
        products = lines.product_id
        if lines and all(line.product_id for line in lines):
            # every product is known: only the lines that can be the origin
            domain.append(("product_id", "in", products.ids))
        action["domain"] = domain
        action["context"] = dict(
            safe_eval(action["context"]), match_document_id=self.id
        )
        action["name"] = _("Match with Orders: %s", self.display_name)
        return action
