# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_STATE_CANCEL,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_INUTILIZADA,
)

# an origin that a person decided is never replaced by a suggestion
DECIDED_ORIGIN_STATES = ("resolved", "no_order")


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    import_purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        string="Purchase Order Line (origin)",
        copy=False,
        index=True,
        ondelete="set null",
        domain="['|', ('id', 'in', import_origin_candidate_ids),"
        " ('id', '=', import_purchase_line_id)]",
        help="Purchase order line this imported document line corresponds to. "
        "It is suggested from the order reference of the file (xPed and "
        "nItemPed) or from the only open order line of the supplier for the "
        "product, and a person confirms or changes it.",
    )

    import_origin_state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("suggested", "Suggested"),
            ("resolved", "Resolved"),
            ("no_order", "Without Order"),
        ],
        string="Origin State",
        copy=False,
        index=True,
        help="Review of the origin of an imported line. Pending: the supplier "
        "has open order lines and none was chosen. Suggested: an automatic "
        "suggestion waits for confirmation. Resolved: a person chose it, or the "
        "supplier declared it with no doubt (order and item of the file). "
        "Without Order: a person decided there is no order. Empty when there is "
        "nothing to choose from.",
    )

    import_origin_candidate_ids = fields.Many2many(
        comodel_name="purchase.order.line",
        compute="_compute_import_origin_candidate_ids",
        help="Technical: the open purchase order lines the origin can be chosen "
        "from (supplier of the document, product of the line, company, "
        "confirmed order with a balance to invoice).",
    )

    @api.depends(
        "document_id.partner_id",
        "document_id.company_id",
        "document_id.fiscal_operation_type",
        "document_id.issuer",
        "product_id",
    )
    def _compute_import_origin_candidate_ids(self):
        # one reading for all the lines, not one search for each of them
        pool = self._import_origin_pool()
        for line in self:
            line.import_origin_candidate_ids = line._import_origin_candidates(pool)

    @api.constrains("import_purchase_line_id")
    def _check_import_purchase_line(self):
        """What the domain of the field only suggests to the client: the order
        line is of the company and of the supplier of the document, and of the
        product of the line."""
        for line in self.filtered("import_purchase_line_id"):
            order_line = line.import_purchase_line_id.sudo()
            document = line.document_id
            if (
                order_line.company_id != document.company_id
                or order_line.order_id.partner_id.commercial_partner_id
                != document.partner_id.commercial_partner_id
            ):
                raise ValidationError(
                    _(
                        "The order line %(order_line)s is not of the company and "
                        "of the supplier of the document.",
                        order_line=order_line.display_name,
                    )
                )
            if line.product_id and line.product_id != order_line.product_id:
                raise ValidationError(
                    _(
                        "The order line %(order_line)s is not of the product of "
                        "the line %(line)s.",
                        order_line=order_line.display_name,
                        line=line.name,
                    )
                )

    def write(self, vals):
        if (
            "import_purchase_line_id" in vals
            and "import_origin_state" not in vals
            and not self.env.context.get("import_origin_suggestion")
        ):
            # a person picked (or cleared) the origin on the line
            vals = dict(
                vals,
                import_origin_state=(
                    "resolved" if vals["import_purchase_line_id"] else "pending"
                ),
            )
        result = super().write(vals)
        if vals.get("import_origin_state") == "resolved":
            self.filtered(
                lambda line: line.import_origin_state == "resolved"
            )._apply_import_origin_operation_line()
        return result

    def _apply_import_origin_operation_line(self):
        """The destination of the order goes into the imported line.

        The operation line of an imported line is the default one of the
        operation and does not know what the order was bought for. The line
        takes the one of the order line, unless a person chose another one, or
        a bill already exists.
        """
        for line in self:
            wanted = line.import_purchase_line_id.sudo().fiscal_operation_line_id
            operation = line.fiscal_operation_id
            if (
                not wanted
                or wanted == line.fiscal_operation_line_id
                or wanted.fiscal_operation_id != operation
                or line.document_id.sudo().move_ids
            ):
                continue
            default = operation.line_definition(
                company=line.company_id,
                partner=line.partner_id,
                product=line.product_id,
            )
            if line.fiscal_operation_line_id == default:
                line.fiscal_operation_line_id = wanted

    def _import_origin_key(self):
        """(company, supplier) whose open order lines the line can take its
        origin from; False for an outgoing document or one with no partner."""
        self.ensure_one()
        document = self.document_id
        partner = document.partner_id.commercial_partner_id
        # an imported document may still have no fiscal operation; one issued by
        # the company is a sale, whatever the file
        if (
            not partner
            or document.issuer == DOCUMENT_ISSUER_COMPANY
            or document.fiscal_operation_type not in ("in", False)
        ):
            return False
        return (document.company_id.id, partner.id)

    def _import_origin_pool(self):
        """The open order lines the lines of ``self`` can take their origin
        from, and the quantity the other documents already claimed on them.

        Everything is read once for all the lines (one search per supplier and
        company, one for the claims). The fiscal profile that imports the file
        may have no access to the purchase orders: they are only read, with
        sudo.
        """
        order_line_model = self.env["purchase.order.line"].sudo()
        orders = {}
        for line in self:
            key = line._import_origin_key()
            if key and key not in orders:
                orders[key] = order_line_model.search(
                    [
                        ("order_id.state", "in", ("purchase", "done")),
                        ("order_id.company_id", "=", key[0]),
                        ("order_id.partner_id.commercial_partner_id", "=", key[1]),
                        ("display_type", "=", False),
                    ]
                )
        order_lines = order_line_model.browse()
        for found in orders.values():
            order_lines |= found
        claims = defaultdict(list)
        for claimant in self._import_claimants(order_lines):
            claims[claimant.import_purchase_line_id.id].append(
                (claimant.id, claimant._import_claimed_quantity())
            )
        return {"orders": orders, "claims": claims}

    @api.model
    def _import_claimants(self, order_lines):
        """The lines of imported documents that resolved their origin to the
        order lines and have no bill yet: the bill counts what it takes as
        invoiced, but until it exists the document only holds the claim."""
        if not order_lines:
            return self.browse()
        return (
            self.sudo()
            .search(
                [
                    ("import_purchase_line_id", "in", order_lines.ids),
                    ("import_origin_state", "=", "resolved"),
                    ("document_id.imported_document", "=", True),
                    (
                        "document_id.state_edoc",
                        "not in",
                        (
                            DOCUMENT_STATE_CANCEL,
                            SITUACAO_EDOC_DENEGADA,
                            SITUACAO_EDOC_INUTILIZADA,
                        ),
                    ),
                ]
            )
            .filtered(
                lambda claimant: not claimant.document_id.move_ids.filtered(
                    lambda bill: bill.state != "cancel"
                )
            )
        )

    def _import_claimed_quantity(self, order_line=None):
        """The quantity of the line, in the unit of the order line it points to."""
        self.ensure_one()
        order_line = order_line or self.import_purchase_line_id
        if not self.uom_id or not order_line.product_uom:
            return self.quantity
        return self.uom_id._compute_quantity(
            self.quantity, order_line.product_uom, raise_if_failure=False
        )

    def _import_origin_balance(self, order_line, pool):
        """What is left of the order line for this line: the ordered quantity
        less what the bills invoiced and the other documents claimed."""
        self.ensure_one()
        claimed = sum(
            quantity
            for claimant_id, quantity in pool["claims"].get(order_line.id, ())
            if claimant_id != self.id
        )
        return order_line.product_qty - order_line.qty_invoiced - claimed

    def _import_origin_candidates(self, pool=None):
        """Open order lines of the supplier for the line product, with a
        balance left."""
        self.ensure_one()
        empty = self.env["purchase.order.line"]
        key = self._import_origin_key()
        if not key:
            return empty
        pool = pool or self._import_origin_pool()
        order_lines = pool["orders"].get(key, empty)
        if self.product_id:
            order_lines = order_lines.filtered(
                lambda order_line: order_line.product_id == self.product_id
            )
        return order_lines.filtered(
            lambda order_line: float_compare(
                self._import_origin_balance(order_line, pool),
                0.0,
                precision_rounding=order_line.product_uom.rounding,
            )
            > 0
        )

    def _find_purchase_line_by_reference(self):
        self.ensure_one()
        document = self.document_id
        return (
            self.env["purchase.order.line"]
            .sudo()
            ._find_by_import_reference(
                document.company_id,
                document.partner_id.commercial_partner_id,
                (self.partner_order or "").strip(),
                self.partner_order_line,
                self.product_id,
            )
        )

    def action_open_import_origin(self):
        """Open the origin of the line, resolved or suggested: the purchase order
        of the order line. The link modules put their own record first (a
        receipt, a purchase request) when the line has one."""
        self.ensure_one()
        order = self.sudo().import_purchase_line_id.order_id
        if not order:
            raise UserError(_("The line has no origin to open."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "res_id": order.id,
            "views": [(False, "form")],
            "target": "current",
        }

    def _find_purchase_line_by_declared_item(self):
        """The only confirmed order line that the file declares by order and item
        (xPed and nItemPed), whatever the product of the line: the declaration
        names the item, so it names the product too."""
        self.ensure_one()
        document = self.document_id
        if (
            not self._import_origin_key()
            or not (self.partner_order or "").strip()
            or not "".join(
                char for char in (self.partner_order_line or "") if char.isdigit()
            )
        ):
            return self.env["purchase.order.line"]
        return (
            self.env["purchase.order.line"]
            .sudo()
            ._find_by_import_reference(
                document.company_id,
                document.partner_id.commercial_partner_id,
                self.partner_order.strip(),
                self.partner_order_line,
                None,
            )
        )

    def _suggest_import_origin(self):
        """Suggest the origin of an imported line, never replacing a decision.

        The reference of the file (xPed and nItemPed) wins: when it points to
        exactly one open line with the product the origin is resolved, the
        supplier declared it. Without it, the only open order line of the
        supplier for the product is just suggested; otherwise the line waits
        for a decision, and with nothing to choose from it has no origin state.
        Nothing is inferred by value, and xPed and nItemPed stay as they came.
        """
        lines = self.filtered(
            lambda line: line._is_imported()
            and line.import_origin_state not in DECIDED_ORIGIN_STATES
            and (
                not line.import_purchase_line_id
                or line.import_origin_state == "suggested"
            )
        )
        pool = lines._import_origin_pool()
        for line in lines:
            order_line = line._find_purchase_line_by_reference()
            candidates = line._import_origin_candidates(pool)
            key = line._import_origin_key()
            if order_line:
                state = "resolved"
            elif len(candidates) == 1:
                order_line = candidates
                state = "suggested"
            elif candidates or (key and pool["orders"].get(key)):
                state = "pending"
            else:
                state = False
            line.with_context(import_origin_suggestion=True).write(
                {
                    "import_purchase_line_id": order_line.id or False,
                    "import_origin_state": state,
                }
            )
            if state == "resolved":
                pool["claims"][order_line.id].append(
                    (line.id, line._import_claimed_quantity(order_line))
                )

    def _apply_import_depara(self, *args, **kwargs):
        result = super()._apply_import_depara(*args, **kwargs)
        # a product decided on the line may open a candidate
        self._suggest_import_origin()
        return result
