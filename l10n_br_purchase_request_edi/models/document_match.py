# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_purchase_edi.models.document_match import SOURCE_COUNT

SOURCE_REQUEST = 3


class DocumentMatch(models.Model):
    _inherit = "l10n_br_purchase_edi.match"

    kind = fields.Selection(selection_add=[("request", "Purchase Request")])
    line_state = fields.Selection(
        selection_add=[
            ("request_approved", "Request Approved"),
            ("request_in_progress", "Request in Progress"),
        ]
    )
    purchase_request_line_id = fields.Many2one(
        comodel_name="purchase.request.line",
        string="Request Line",
        readonly=True,
        groups="purchase_request.group_purchase_request_user",
    )
    requested_by_id = fields.Many2one(
        comodel_name="res.users", string="Requested by", readonly=True
    )

    @api.model
    def _match_extra_columns(self):
        columns = super()._match_extra_columns()
        columns.update(
            {"purchase_request_line_id": "integer", "requested_by_id": "integer"}
        )
        return columns

    @api.model
    def _match_sources(self):
        sources = super()._match_sources()
        sources.append(
            (
                self._match_request_query(),
                ("purchase_request_line_id", "requested_by_id"),
            )
        )
        return sources

    @api.model
    def _match_request_query(self):
        """Lines of approved requests with a quantity still without order: the
        origin of a purchase made outside the system. The preferred supplier of
        the product, when there is one, is the partner of the row."""
        balance = "prl.product_qty - COALESCE(bought.quantity, 0)"
        return f"""
            SELECT
                {SOURCE_COUNT} * prl.id + {SOURCE_REQUEST} AS id,
                'request' AS kind,
                pr.company_id AS company_id,
                rp.commercial_partner_id AS partner_id,
                prl.product_id AS product_id,
                prl.name AS description,
                NULL::varchar AS declared_reference,
                prl.product_uom_id AS uom_id,
                prl.product_qty AS quantity,
                {balance} AS open_quantity,
                CASE WHEN prl.product_qty > 0
                    THEN prl.estimated_cost / prl.product_qty ELSE 0 END AS price_unit,
                rc.currency_id AS currency_id,
                pr.name AS reference,
                prl.date_required AS date,
                'request_' || pr.state AS line_state,
                NULL::integer AS fiscal_document_id,
                NULL::integer AS fiscal_line_id,
                NULL::integer AS purchase_order_id,
                NULL::integer AS purchase_line_id,
                NULL::integer AS suggested_purchase_line_id,
                prl.id AS purchase_request_line_id,
                pr.requested_by AS requested_by_id
            FROM purchase_request_line prl
            JOIN purchase_request pr ON pr.id = prl.request_id
            JOIN res_company rc ON rc.id = pr.company_id
            LEFT JOIN res_partner rp ON rp.id = prl.supplier_id
            LEFT JOIN (
                SELECT rel.purchase_request_line_id AS request_line_id,
                    SUM(pl.product_qty / pu.factor * ru.factor) AS quantity
                FROM purchase_request_purchase_order_line_rel rel
                JOIN purchase_order_line pl ON pl.id = rel.purchase_order_line_id
                JOIN purchase_request_line r2 ON r2.id = rel.purchase_request_line_id
                JOIN uom_uom pu ON pu.id = pl.product_uom
                JOIN uom_uom ru ON ru.id = r2.product_uom_id
                WHERE pl.state != 'cancel' AND pu.category_id = ru.category_id
                GROUP BY rel.purchase_request_line_id
            ) bought ON bought.request_line_id = prl.id
            WHERE pr.state IN ('approved', 'in_progress')
                AND NOT COALESCE(prl.cancelled, false)
                AND {balance} > 0
        """

    @api.model
    def _origin_fields(self):
        return super()._origin_fields() | {"import_request_line_id"}

    def _check_no_request(self):
        if self.sudo().filtered(lambda row: row.kind == "request"):
            raise UserError(
                _(
                    "A purchase request is not a commitment to the supplier: use "
                    "Create Order from Request."
                )
            )

    def action_match(self):
        self._check_no_request()
        return super().action_match()

    def action_create_order(self):
        self._check_no_request()
        return super().action_create_order()

    def action_create_order_from_request(self):
        """Create the purchase order of the request line with the supplier, the
        quantity and the price of the document lines, and match them to it.

        The order is confirmed, which follows the approval of the company: an
        order that waits for it leaves the lines only suggested, and they are
        resolved when it is confirmed.
        """
        if not self.env.su and not self.env.user.has_group(
            "purchase_request.group_purchase_request_user"
        ):
            raise UserError(_("You have no access to the purchase requests."))
        rows = self._check_selection_access()
        request = rows.filtered(
            lambda row: row.kind == "request"
        ).purchase_request_line_id
        notes, orders, quotes = self._split_selection()
        if len(request) != 1 or not notes or orders or quotes:
            raise UserError(
                _("Select the invoice lines and one purchase request line.")
            )
        document = self._editable_document(notes)
        self._check_units(notes)
        self._check_request(request, notes, document)
        self._check_product_decision(notes)
        uom = request.product_uom_id or request.product_id.uom_id
        quantity = sum(
            line.uom_id._compute_quantity(line.quantity, uom)
            if line.uom_id
            else line.quantity
            for line in notes
        )
        amount = sum(line.quantity * line.price_unit for line in notes)
        order = self._create_order_from_request(request, document, quantity, amount)
        order_line = order.order_line
        confirmed = order.state in ("purchase", "done")
        for line in notes:
            if not line.product_id:
                factor = (
                    line.uom_id._compute_quantity(1.0, order_line.product_uom)
                    if line.uom_id
                    else 1.0
                )
                line._apply_import_depara(
                    product=request.product_id,
                    uom=order_line.product_uom,
                    factor=factor,
                )
            self._write_origin(
                line,
                {
                    "import_purchase_line_id": order_line.id,
                    "import_origin_state": "resolved" if confirmed else "suggested",
                    "import_request_line_id": request.id,
                },
            )
        document.message_post(
            body=_(
                "Order %(order)s created from the purchase request %(request)s "
                "and matched to %(count)s line(s)%(waiting)s.",
                order=order.name,
                request=request.request_id.name,
                count=len(notes),
                waiting="" if confirmed else _(", waiting for its approval"),
            )
        )
        return {
            "type": "ir.actions.act_window",
            "name": order.name,
            "res_model": "purchase.order",
            "res_id": order.id,
            "view_mode": "form",
        }

    @api.model
    def _check_request(self, request, notes, document):
        if request.company_id != document.company_id:
            raise UserError(
                _("The request line is of another company than the document.")
            )
        if request.cancelled or request.request_id.state not in (
            "approved",
            "in_progress",
        ):
            raise UserError(
                _("The purchase request %s is not approved.") % request.request_id.name
            )
        if not request.product_id:
            raise UserError(_("The request line has no product."))
        uom = request.product_uom_id or request.product_id.uom_id
        for line in notes:
            if line.product_id and line.product_id != request.product_id:
                raise UserError(
                    _(
                        "The product of the line %(line)s is not the product of "
                        "the request line.",
                        line=line.name,
                    )
                )
            if line.uom_id and line.uom_id.category_id != uom.category_id:
                raise UserError(
                    _(
                        "The unit of the line %(line)s does not convert to the "
                        "unit of the request line.",
                        line=line.name,
                    )
                )

    @api.model
    def _create_order_from_request(self, request, document, quantity, amount):
        """The order of the request wizard, with the supplier, the quantity and
        the price of the document, confirmed."""
        wizard = (
            self.env["purchase.request.line.make.purchase.order"]
            .with_company(document.company_id)
            .with_context(active_model="purchase.request.line", active_ids=request.ids)
            .create({"supplier_id": document.partner_id.id})
        )
        wizard.item_ids.product_qty = min(
            quantity, request.pending_qty_to_receive or quantity
        )
        domain = wizard.make_purchase_order()["domain"]
        order = self.env["purchase.order"].search(domain)
        order_line = order.order_line
        uom = request.product_uom_id or request.product_id.uom_id
        order_line.write(
            {
                "product_qty": uom._compute_quantity(quantity, order_line.product_uom),
                "price_unit": uom._compute_price(
                    amount / quantity, order_line.product_uom
                ),
            }
        )
        order.write(
            {
                "date_order": document.document_date or fields.Datetime.now(),
                "origin": ", ".join(
                    filter(
                        None,
                        [order.origin, _("Fiscal document %s") % document.display_name],
                    )
                ),
            }
        )
        order.button_confirm()
        return order
