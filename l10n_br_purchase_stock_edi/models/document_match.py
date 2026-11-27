# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_purchase_edi.models.document_match import SOURCE_COUNT

SOURCE_RECEIPT = 2


class DocumentMatch(models.Model):
    _inherit = "l10n_br_purchase_edi.match"

    kind = fields.Selection(selection_add=[("receipt", "Receipt")])
    line_state = fields.Selection(
        selection_add=[
            ("receipt_pending", "To Receive"),
            ("receipt_done", "Received"),
        ]
    )
    stock_move_id = fields.Many2one(
        comodel_name="stock.move", string="Receipt Move", readonly=True
    )
    picking_id = fields.Many2one(
        comodel_name="stock.picking", string="Receipt", readonly=True
    )

    @api.model
    def _match_extra_columns(self):
        columns = super()._match_extra_columns()
        columns.update({"stock_move_id": "integer", "picking_id": "integer"})
        return columns

    @api.model
    def _match_sources(self):
        sources = super()._match_sources()
        sources.append((self._match_receipt_query(), ("stock_move_id", "picking_id")))
        return sources

    @api.model
    def _match_receipt_query(self):
        """Incoming moves of confirmed order lines: the ones still to receive
        and the received ones that are not invoiced yet. Returns (outgoing)
        and cancelled moves stay out."""
        quantity = (
            "CASE WHEN sm.state = 'done' THEN COALESCE((SELECT SUM(sml.qty_done) "
            "FROM stock_move_line sml WHERE sml.move_id = sm.id), 0) "
            "ELSE sm.product_uom_qty END"
        )
        return f"""
            SELECT
                {SOURCE_COUNT} * sm.id + {SOURCE_RECEIPT} AS id,
                'receipt' AS kind,
                sm.company_id AS company_id,
                rp.commercial_partner_id AS partner_id,
                sm.product_id AS product_id,
                sm.name AS description,
                NULL::varchar AS declared_reference,
                sm.product_uom AS uom_id,
                {quantity} AS quantity,
                {quantity} AS open_quantity,
                pl.price_unit AS price_unit,
                po.currency_id AS currency_id,
                COALESCE(sp.name, sm.name) AS reference,
                sm.date::date AS date,
                CASE WHEN sm.state = 'done' THEN 'receipt_done'
                    ELSE 'receipt_pending' END AS line_state,
                NULL::integer AS fiscal_document_id,
                NULL::integer AS fiscal_line_id,
                po.id AS purchase_order_id,
                pl.id AS purchase_line_id,
                NULL::integer AS suggested_purchase_line_id,
                sm.id AS stock_move_id,
                sm.picking_id AS picking_id
            FROM stock_move sm
            JOIN purchase_order_line pl ON pl.id = sm.purchase_line_id
            JOIN purchase_order po ON po.id = pl.order_id
            JOIN res_partner rp ON rp.id = po.partner_id
            JOIN stock_picking_type spt ON spt.id = sm.picking_type_id
            LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
            WHERE spt.code = 'incoming'
                AND sm.state != 'cancel'
                AND pl.display_type IS NULL
                AND po.state IN ('purchase', 'done')
                AND (sm.state != 'done' OR pl.qty_received - pl.qty_invoiced > 0)
        """

    @api.model
    def _origin_fields(self):
        return super()._origin_fields() | {
            "import_stock_move_id",
            "import_no_stock_entry",
        }

    def action_match(self):
        """With a receipt move selected the origin takes it, instead of the one
        candidate of the order line."""
        rows = self._check_selection_access()
        receipts = rows.filtered(lambda row: row.kind == "receipt").stock_move_id
        if receipts:
            order_lines = rows.filtered(
                lambda row: row.kind == "order"
            ).purchase_line_id
            if len(receipts) > 1:
                raise UserError(_("Select one receipt move."))
            if receipts.purchase_line_id != order_lines or not order_lines:
                raise UserError(
                    _("The receipt move does not belong to the selected order line.")
                )
        result = super().action_match()
        if receipts:
            self._write_origin(
                rows.filtered(lambda row: row.kind == "note").fiscal_line_id,
                {"import_stock_move_id": receipts.id},
            )
        return result

    def action_open_receipt(self):
        """Open the receipt of the selected lines with the quantities and the
        lots of the document proposed. Nothing is validated."""
        rows = self._check_selection_access()
        moves = (
            rows.filtered(lambda row: row.kind == "receipt").stock_move_id
            | rows.filtered(
                lambda row: row.kind == "note"
            ).fiscal_line_id.import_stock_move_id
        )
        picking = moves.picking_id
        if not moves:
            raise UserError(_("Select lines that have a receipt."))
        if len(picking) != 1:
            raise UserError(_("Select the lines of one receipt."))
        moves._propose_from_import()
        return {
            "type": "ir.actions.act_window",
            "name": picking.name,
            "res_model": "stock.picking",
            "res_id": picking.id,
            "view_mode": "form",
        }

    def action_create_receipt(self):
        """Create the receipt of a stockable product bought with no order: an
        incoming picking, confirmed and not validated."""
        lines = self._split_selection()[0]
        if not lines:
            raise UserError(_("Select the invoice lines to create the receipt."))
        document = self._editable_document(lines)
        self._check_units(lines)
        if not all(
            line.import_origin_state == "no_order"
            and not line.import_stock_move_id
            and line.product_id.detailed_type == "product"
            for line in lines
        ):
            raise UserError(
                _(
                    "A receipt is created for lines of stockable products marked "
                    "as without order and with no receipt yet."
                )
            )
        company = document.company_id
        picking_type = (
            self.env["stock.warehouse"]
            .search([("company_id", "=", company.id)], limit=1)
            .in_type_id
        )
        if not picking_type:
            raise UserError(_("The company has no warehouse."))
        supplier = self.env.ref("stock.stock_location_suppliers")
        from_location = picking_type.default_location_src_id or supplier
        picking = (
            self.env["stock.picking"]
            .with_company(company)
            .create(
                {
                    "picking_type_id": picking_type.id,
                    "partner_id": document.partner_id.id,
                    "location_id": from_location.id,
                    "location_dest_id": picking_type.default_location_dest_id.id,
                    "origin": _("Fiscal document %s") % document.display_name,
                    "move_ids": [
                        Command.create(
                            self._prepare_receipt_move_vals(
                                line, picking_type, from_location
                            )
                        )
                        for line in lines
                    ],
                }
            )
        )
        picking.action_confirm()
        for line, move in zip(lines, picking.move_ids.sorted("id"), strict=True):
            self._write_origin(line, {"import_stock_move_id": move.id})
        document.message_post(
            body=_("Receipt %(picking)s created for %(count)s line(s).")
            % {"picking": picking.name, "count": len(lines)}
        )
        return {
            "type": "ir.actions.act_window",
            "name": picking.name,
            "res_model": "stock.picking",
            "res_id": picking.id,
            "view_mode": "form",
        }

    @api.model
    def _prepare_receipt_move_vals(self, line, picking_type, from_location):
        """Quantity and cost of the document line, in the unit of the product."""
        product = line.product_id
        quantity, price = line.quantity, line.price_unit
        if line.uom_id and line.uom_id.category_id == product.uom_id.category_id:
            quantity = line.uom_id._compute_quantity(quantity, product.uom_id)
            price = line.uom_id._compute_price(price, product.uom_id)
        return {
            "name": line.name,
            "product_id": product.id,
            "product_uom": product.uom_id.id,
            "product_uom_qty": quantity,
            "price_unit": price,
            "company_id": picking_type.company_id.id,
            "picking_type_id": picking_type.id,
            "location_id": from_location.id,
            "location_dest_id": picking_type.default_location_dest_id.id,
        }

    def action_no_stock_entry(self):
        """A purchase or stock manager decides that the goods do not enter the
        stock: the only place where this decision is taken."""
        user = self.env.user
        if not (
            user.has_group("purchase.group_purchase_manager")
            or user.has_group("stock.group_stock_manager")
        ):
            raise UserError(
                _(
                    "Only a purchase manager or a stock manager can mark a line "
                    "as without stock entry."
                )
            )
        lines = self._split_selection()[0].filtered(
            lambda line: line.import_origin_state == "no_order"
        )
        if not lines:
            raise UserError(_("Select invoice lines marked as without order."))
        document = self._editable_document(lines)
        self._write_origin(lines, {"import_no_stock_entry": True})
        document.message_post(
            body=_("%s line(s) marked as without stock entry.", len(lines))
        )
        return True
