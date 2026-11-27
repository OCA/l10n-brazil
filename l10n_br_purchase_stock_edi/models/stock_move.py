# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, time

from odoo import _, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _import_document_lines(self):
        """Lines of imported documents that point to this receipt move."""
        self.ensure_one()
        return (
            self.env["l10n_br_fiscal.document.line"]
            .sudo()
            .search([("import_stock_move_id", "=", self.id)])
        )

    def _edi_lot_values(self, lot):
        """What to write on the move line for a lot the document declared.

        The receipt type decides: an existing lot is used by its id; a type
        that creates lots on validation gets the lot name (no stock.lot yet);
        only a type that does not create lots on validation needs the lot to
        exist now. The expiry date is written only when ``product_expiry`` is
        installed.
        """
        self.ensure_one()
        Lot = self.env["stock.lot"]
        expiry = "expiration_date" in Lot._fields and lot.date_expiry
        expiration = datetime.combine(lot.date_expiry, time.min) if expiry else False
        existing = Lot.search(
            [
                ("name", "=", lot.name),
                ("product_id", "=", self.product_id.id),
                ("company_id", "=", self.company_id.id),
            ],
            limit=1,
        )
        if existing:
            return {"lot_id": existing.id}
        vals = {}
        if self.picking_type_id.use_create_lots:
            vals["lot_name"] = lot.name
            if expiration:
                vals["expiration_date"] = expiration
            return vals
        vals = {
            "name": lot.name,
            "product_id": self.product_id.id,
            "company_id": self.company_id.id,
        }
        if expiration:
            vals["expiration_date"] = expiration
        return {"lot_id": Lot.create(vals).id}

    def _import_declared_lots(self):
        """The lots the documents that point to this move declare, with the
        line that declared each one."""
        self.ensure_one()
        return [
            (line, lot)
            for line in self._import_document_lines()
            for lot in line._edi_get_lots()
        ]

    def _propose_lots_from_import(self):
        """Fill the receipt move with the lots the document declared (lot
        number, quantity and expiry date), for the operator to review. Nothing
        is validated.

        Returns the reason why nothing was proposed, or an empty string.
        """
        self.ensure_one()
        if self.state in ("done", "cancel"):
            return _("The receipt move is already closed.")
        if self.product_id.tracking != "lot":
            return _("%s is not tracked by lot.", self.product_id.display_name)
        if any(
            line.lot_id
            or line.lot_name
            or line.qty_done
            or line.package_id
            or line.result_package_id
            for line in self.move_line_ids
        ):
            return _(
                "The receipt of %s already has lots or quantities.",
                self.product_id.display_name,
            )
        proposals = [
            (
                document_line.uom_id._compute_quantity(lot.quantity, self.product_uom),
                document_line.uom_id._compute_quantity(
                    lot.quantity, self.product_id.uom_id
                ),
                self._edi_lot_values(lot),
            )
            for document_line, lot in self._import_declared_lots()
        ]
        if not proposals:
            return _(
                "The document has no lot declared for %s.",
                self.product_id.display_name,
            )
        # the empty lines already there are reused, so that the move keeps its
        # reservation and does not leave the Ready state
        empty_lines = self.move_line_ids
        for index, (quantity, product_quantity, values) in enumerate(proposals):
            line_values = dict(values, qty_done=quantity, reserved_uom_qty=quantity)
            if index < len(empty_lines):
                empty_lines[index].write(line_values)
            else:
                vals = self._prepare_move_line_vals(quantity=product_quantity)
                vals.update(line_values)
                self.env["stock.move.line"].create(vals)
        empty_lines[len(proposals) :].unlink()
        # a move from a supplier is always reservable: the remainder of the
        # quantity, if any, gets its own line and the move stays assigned
        self._action_assign()
        return ""

    def _propose_from_import(self):
        """Propose the lots of the document on the moves tracked by lot and the
        quantity of the document on the others. Only a move with nothing done yet
        receives it, and nothing is validated."""
        for move in self:
            lines = move._import_document_lines()
            if not lines or move.state in ("done", "cancel"):
                continue
            if move.product_id.tracking == "lot":
                move._propose_lots_from_import()
            elif not move.quantity_done:
                move.quantity_done = sum(
                    line.uom_id._compute_quantity(
                        line.quantity, move.product_uom, raise_if_failure=False
                    )
                    for line in lines
                )
