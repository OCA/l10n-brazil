# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_STATE_CANCEL,
    DOCUMENT_STATE_DRAFT,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_INUTILIZADA,
)

# Ids encode the source: id = SOURCE_COUNT * source id + source type. A module
# that adds a source (receipt, purchase request) takes the next type.
SOURCE_COUNT = 4
SOURCE_NOTE = 0
SOURCE_ORDER_LINE = 1

# The columns every source gives, in this order.
MATCH_COLUMNS = (
    "id",
    "kind",
    "company_id",
    "partner_id",
    "product_id",
    "description",
    "declared_reference",
    "uom_id",
    "quantity",
    "open_quantity",
    "price_unit",
    "currency_id",
    "reference",
    "date",
    "line_state",
    "fiscal_document_id",
    "fiscal_line_id",
    "purchase_order_id",
    "purchase_line_id",
    "suggested_purchase_line_id",
)


class DocumentMatch(models.Model):
    """Read model: what the system knows about where an imported document came
    from. Lines of the document waiting for an origin, and the lines of
    confirmed orders (with their balance) and of quotations of the supplier,
    side by side. Each module that knows another source adds a ``SELECT`` to
    ``_match_queries``.
    """

    _name = "l10n_br_purchase_edi.match"
    _description = "Origin of an imported fiscal document"
    _auto = False
    _order = "product_id, kind, reference"

    kind = fields.Selection(
        selection=[
            ("note", "Invoice"),
            ("order", "Order"),
            ("quote", "Quotation"),
        ],
        readonly=True,
    )
    company_id = fields.Many2one(comodel_name="res.company", readonly=True)
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier",
        readonly=True,
        help="Commercial partner of the document or of the order.",
    )
    product_id = fields.Many2one(comodel_name="product.product", readonly=True)
    description = fields.Char(readonly=True)
    declared_reference = fields.Char(
        string="Supplier Reference",
        readonly=True,
        help="Order and item the supplier declared in the file (xPed, nItemPed).",
    )
    uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit", readonly=True)
    quantity = fields.Float(readonly=True, digits="Product Unit of Measure")
    open_quantity = fields.Float(
        string="Balance",
        readonly=True,
        digits="Product Unit of Measure",
        help="Order: ordered less invoiced less claimed by the other imported "
        "documents that have no bill yet.",
    )
    price_unit = fields.Float(string="Price", readonly=True, digits="Product Price")
    note_quantity = fields.Float(
        compute="_compute_note_comparison",
        digits="Product Unit of Measure",
        help="Quantity of the line of the document being matched (context) for "
        "the same product, in the unit of this row.",
    )
    note_price_unit = fields.Float(
        compute="_compute_note_comparison",
        digits="Product Price",
        help="Price of the line of the document being matched (context) for the "
        "same product, in the unit of this row.",
    )
    quantity_difference = fields.Float(
        compute="_compute_note_comparison",
        digits="Product Unit of Measure",
        help="Quantity of the document less the balance of the order line.",
    )
    price_difference = fields.Float(
        compute="_compute_note_comparison",
        digits="Product Price",
        help="Price of the order line or quotation less the price of the line of "
        "the document being matched (context) for the same product, in the "
        "unit of the row.",
    )
    price_difference_percent = fields.Float(
        compute="_compute_note_comparison",
        string="Price Difference %",
        help="Price difference as a percentage.",
    )
    hint = fields.Char(
        compute="_compute_note_comparison",
        help="Why the line of the document has no suggestion yet.",
    )
    currency_id = fields.Many2one(comodel_name="res.currency", readonly=True)
    reference = fields.Char(readonly=True)
    date = fields.Date(readonly=True)
    line_state = fields.Selection(
        selection=[
            ("none", "No Open Order"),
            ("pending", "Pending"),
            ("suggested", "Suggested"),
            ("resolved", "Resolved"),
            ("no_order", "Without Order"),
            ("confirmed", "Confirmed"),
            ("draft", "Draft Quotation"),
            ("sent", "Quotation Sent"),
        ],
        string="Situation",
        readonly=True,
    )
    fiscal_document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document", readonly=True
    )
    fiscal_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.line", readonly=True
    )
    purchase_order_id = fields.Many2one(
        comodel_name="purchase.order", string="Purchase Order", readonly=True
    )
    purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line", string="Order Line", readonly=True
    )
    suggested_purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        string="Origin Chosen",
        readonly=True,
        help="Order line the invoice line points to, suggested or resolved.",
    )

    @property
    def _table_query(self):
        return " UNION ALL ".join(self._match_queries())

    @api.model
    def _match_extra_columns(self):
        """The columns that the sources of other modules add, as
        ``{name: SQL type}``. A module that adds a column (and its field) extends
        this with ``super()``; the sources that do not give it have it empty."""
        return {}

    @api.model
    def _match_sources(self):
        """The sources, as ``[(SELECT, names of the extra columns it gives)]``.
        Each ``SELECT`` gives ``MATCH_COLUMNS`` and the extra columns it names; a
        module that adds a source extends this list with ``super()``."""
        return [(self._match_note_query(), ()), (self._match_order_query(), ())]

    @api.model
    def _match_queries(self):
        """The ``SELECT`` of each source, all with the same columns."""
        extras = self._match_extra_columns()
        queries = []
        for select, given in self._match_sources():
            columns = [f"q.{name}" for name in MATCH_COLUMNS]
            columns += [
                f"q.{name}" if name in given else f"NULL::{sql_type} AS {name}"
                for name, sql_type in extras.items()
            ]
            queries.append(f"SELECT {', '.join(columns)} FROM ({select}) q")
        return queries

    @api.model
    def _match_note_query(self):
        return f"""
            SELECT
                {SOURCE_COUNT} * fl.id + {SOURCE_NOTE} AS id,
                'note' AS kind,
                fd.company_id AS company_id,
                rp.commercial_partner_id AS partner_id,
                fl.product_id AS product_id,
                fl.name AS description,
                NULLIF(CONCAT_WS(' / ', NULLIF(fl.partner_order, ''),
                    NULLIF(fl.partner_order_line, '')), '') AS declared_reference,
                fl.uom_id AS uom_id,
                fl.quantity AS quantity,
                fl.quantity AS open_quantity,
                fl.price_unit AS price_unit,
                rc.currency_id AS currency_id,
                COALESCE(fd.document_number, fd.document_key) AS reference,
                fd.document_date::date AS date,
                COALESCE(fl.import_origin_state, 'none') AS line_state,
                fd.id AS fiscal_document_id,
                fl.id AS fiscal_line_id,
                NULL::integer AS purchase_order_id,
                NULL::integer AS purchase_line_id,
                fl.import_purchase_line_id AS suggested_purchase_line_id
            FROM l10n_br_fiscal_document_line fl
            JOIN l10n_br_fiscal_document fd ON fd.id = fl.document_id
            JOIN res_partner rp ON rp.id = fd.partner_id
            JOIN res_company rc ON rc.id = fd.company_id
            WHERE fd.imported_document
                AND fd.issuer = 'partner'
                AND COALESCE(fd.fiscal_operation_type, 'in') = 'in'
                AND COALESCE(fd.edoc_purpose, '1') = '1'
                AND fd.state_edoc = '{DOCUMENT_STATE_DRAFT}'
                AND NOT EXISTS (
                    SELECT 1 FROM account_move am
                    WHERE am.fiscal_document_id = fd.id AND am.state != 'cancel'
                )
        """

    @api.model
    def _match_claims_query(self):
        """Quantity of each order line that imported documents without a bill
        resolved to, in the unit of the order line."""
        return f"""
            SELECT fl.import_purchase_line_id AS purchase_line_id,
                SUM(fl.quantity * CASE
                    WHEN fu.id IS NOT NULL AND fu.category_id = pu.category_id
                    THEN pu.factor / fu.factor ELSE 1 END) AS quantity
            FROM l10n_br_fiscal_document_line fl
            JOIN l10n_br_fiscal_document fd ON fd.id = fl.document_id
            JOIN purchase_order_line pl ON pl.id = fl.import_purchase_line_id
            LEFT JOIN uom_uom pu ON pu.id = pl.product_uom
            LEFT JOIN uom_uom fu ON fu.id = fl.uom_id
            WHERE fl.import_origin_state = 'resolved'
                AND fd.imported_document
                AND fd.state_edoc NOT IN ('{DOCUMENT_STATE_CANCEL}',
                    '{SITUACAO_EDOC_DENEGADA}', '{SITUACAO_EDOC_INUTILIZADA}')
                AND NOT EXISTS (
                    SELECT 1 FROM account_move am
                    WHERE am.fiscal_document_id = fd.id AND am.state != 'cancel'
                )
            GROUP BY fl.import_purchase_line_id
        """

    @api.model
    def _match_order_query(self):
        balance = "pl.product_qty - pl.qty_invoiced - COALESCE(claims.quantity, 0)"
        return f"""
            SELECT
                {SOURCE_COUNT} * pl.id + {SOURCE_ORDER_LINE} AS id,
                CASE WHEN po.state IN ('purchase', 'done')
                    THEN 'order' ELSE 'quote' END AS kind,
                po.company_id AS company_id,
                rp.commercial_partner_id AS partner_id,
                pl.product_id AS product_id,
                pl.name AS description,
                NULL::varchar AS declared_reference,
                pl.product_uom AS uom_id,
                pl.product_qty AS quantity,
                {balance} AS open_quantity,
                pl.price_unit AS price_unit,
                po.currency_id AS currency_id,
                po.name AS reference,
                po.date_order::date AS date,
                CASE WHEN po.state IN ('purchase', 'done')
                    THEN 'confirmed' ELSE po.state END AS line_state,
                NULL::integer AS fiscal_document_id,
                NULL::integer AS fiscal_line_id,
                po.id AS purchase_order_id,
                pl.id AS purchase_line_id,
                NULL::integer AS suggested_purchase_line_id
            FROM purchase_order_line pl
            JOIN purchase_order po ON po.id = pl.order_id
            JOIN res_partner rp ON rp.id = po.partner_id
            LEFT JOIN ({self._match_claims_query()}) claims
                ON claims.purchase_line_id = pl.id
            WHERE pl.display_type IS NULL
                AND (po.state IN ('draft', 'sent')
                    OR (po.state IN ('purchase', 'done') AND {balance} > 0))
        """

    @api.depends_context("match_document_id")
    @api.depends("kind", "price_unit", "uom_id", "product_id", "line_state")
    def _compute_note_comparison(self):
        document_id = self.env.context.get("match_document_id")
        notes = self.browse()
        if document_id:
            notes = self.search(
                [("kind", "=", "note"), ("fiscal_document_id", "=", document_id)]
            )
        for row in self:
            row.note_quantity = row.note_price_unit = 0.0
            row.quantity_difference = row.price_difference = 0.0
            row.price_difference_percent = 0.0
            row.hint = False
            if row.kind == "note":
                row.hint = row._note_hint()
                continue
            same = notes.filtered(
                lambda note, row=row: note.product_id == row.product_id
            )
            if len(same) != 1 or not row.uom_id:
                continue
            quantity = same.uom_id._compute_quantity(
                same.quantity, row.uom_id, raise_if_failure=False
            )
            price = same.uom_id._compute_price(same.price_unit, row.uom_id)
            row.note_quantity = quantity
            row.note_price_unit = price
            row.quantity_difference = quantity - row.open_quantity
            row.price_difference = row.price_unit - price
            if price:
                row.price_difference_percent = 100 * (row.price_unit - price) / price

    def _note_hint(self):
        """Why a line of the document waits for a choice: the order lines that
        could be its origin."""
        self.ensure_one()
        if self.line_state != "pending":
            return False
        count = self.search_count(
            [
                ("kind", "=", "order"),
                ("company_id", "=", self.company_id.id),
                ("partner_id", "=", self.partner_id.id),
                ("product_id", "=", self.product_id.id),
            ]
        )
        if count < 2:
            return False
        return _("%s possible order lines: choose one", count)

    # Actions ---------------------------------------------------------------

    def _check_selection_access(self):
        """The rows of the selection, after the access of the real user.

        The rows are read through ``sudo`` (the buyer and the fiscal profile do
        not read each other's models), and a call by id reaches rows that the
        rules of the model would hide, so the selection is first searched as the
        user: a row of another company, or of a model that his group does not
        read, is refused."""
        self.check_access_rights("read")
        ids = set(self.ids)
        if len(self.search([("id", "in", list(ids))])) != len(ids):
            raise AccessError(_("You have no access to some of the selected lines."))
        return self.sudo().browse(list(ids))

    def _split_selection(self):
        """Invoice lines, order lines and quotation lines of the selection, as
        records of the models they come from, read with sudo after the access
        check of the real user (the buyer and the fiscal profile do not read
        each other's models). The writes of the decisions go through
        ``_write_origin``."""
        rows = self._check_selection_access()
        return (
            rows.filtered(lambda row: row.kind == "note").fiscal_line_id,
            rows.filtered(lambda row: row.kind == "order").purchase_line_id,
            rows.filtered(lambda row: row.kind == "quote").purchase_line_id,
        )

    @api.model
    def _origin_fields(self):
        """The only fields of a fiscal line that a decision of the screen
        writes. The link modules add theirs (receipt move, request line)."""
        return {"import_purchase_line_id", "import_origin_state"}

    def _write_origin(self, lines, vals):
        """Write the origin of invoice lines for the real user, which may be a
        buyer with no right on the fiscal lines: only the fields of the origin,
        on lines of a document of an active company of the user."""
        unexpected = set(vals) - self._origin_fields()
        if unexpected:
            raise AccessError(
                _("The screen does not write %s.") % ", ".join(sorted(unexpected))
            )
        if lines.document_id.company_id - self.env.companies:
            raise AccessError(_("You have no access to the documents of the company."))
        lines.sudo().write(vals)

    def _check_product_decision(self, lines):
        """Taking the product of the order line for a line without product is a
        fiscal decision (product, unit and de-para): only for the fiscal group,
        since the ACL of the fiscal lines is open to every internal user."""
        if lines.filtered(lambda line: not line.product_id) and not (
            self.env.su or self.env.user.has_group("l10n_br_fiscal.group_user")
        ):
            raise AccessError(
                _(
                    "Choosing the product of a line is for the fiscal profile. "
                    "Ask for the product to be resolved before matching."
                )
            )

    @api.model
    def _editable_document(self, lines):
        """The one document of the lines, still open to change."""
        document = lines.document_id
        if len(document) != 1:
            raise UserError(_("Select the lines of one document at a time."))
        if document.company_id not in self.env.companies:
            raise AccessError(
                _("You have no access to the documents of the company %s.")
                % document.company_id.name
            )
        if (
            document.state_edoc != DOCUMENT_STATE_DRAFT
            or document.sudo().move_ids.filtered(lambda move: move.state != "cancel")
        ):
            raise UserError(
                _("The document %s is not in draft or already has a bill.")
                % document.display_name
            )
        return document

    @api.model
    def _check_units(self, lines):
        """A unit the supplier declared and nobody confirmed is not converted
        silently: the person chooses it on the line first."""
        for line in lines.filtered(lambda line: line._import_unit_unconfirmed()):
            raise UserError(
                _(
                    "The unit %(unit)s declared for the line %(line)s was not "
                    "confirmed. Choose the unit on the line before using it here.",
                    unit=line.partner_uom_code,
                    line=line.name,
                )
            )

    def action_match(self):
        """Resolve the origin of invoice lines to one confirmed order line."""
        notes, orders, quotes = self._split_selection()
        if quotes:
            raise UserError(
                _(
                    "A quotation cannot be matched until the buyer confirms the "
                    "order. Use Open Quotation."
                )
            )
        if not notes:
            raise UserError(_("Select the invoice lines to match."))
        if len(orders) != 1:
            raise UserError(_("Select one order line to match."))
        document = self._editable_document(notes)
        self._check_units(notes)
        order_line = orders
        if order_line.order_id.state not in ("purchase", "done"):
            raise UserError(
                _("The order %s is not confirmed.") % order_line.order_id.name
            )
        if (
            order_line.company_id != document.company_id
            or order_line.order_id.partner_id.commercial_partner_id
            != document.partner_id.commercial_partner_id
        ):
            raise UserError(
                _("The order line is of another company or of another supplier.")
            )
        for line in notes:
            if line.product_id and line.product_id != order_line.product_id:
                raise UserError(
                    _(
                        "The product of the line %(line)s is not the product of "
                        "the order line.",
                        line=line.name,
                    )
                )
            if (
                line.uom_id
                and line.uom_id.category_id != order_line.product_uom.category_id
            ):
                raise UserError(
                    _(
                        "The unit of the line %(line)s does not convert to the "
                        "unit of the order line.",
                        line=line.name,
                    )
                )
        self._check_product_decision(notes)
        for line in notes:
            if not line.product_id:
                # the product of the order is the decision, learned as a de-para
                factor = (
                    line.uom_id._compute_quantity(1.0, order_line.product_uom)
                    if line.uom_id
                    else 1.0
                )
                line._apply_import_depara(
                    product=order_line.product_id,
                    uom=order_line.product_uom,
                    factor=factor,
                )
            self._write_origin(
                line,
                {
                    "import_purchase_line_id": order_line.id,
                    "import_origin_state": "resolved",
                },
            )
        document.message_post(
            body=_(
                "Origin of %(count)s line(s) matched to the order %(order)s.",
                count=len(notes),
                order=order_line.order_id.name,
            )
        )
        return True

    def action_undo(self):
        """Take back a decision: the origin goes back to pending."""
        lines = self._split_selection()[0].filtered(
            lambda line: line.import_origin_state in ("resolved", "no_order")
        )
        if not lines:
            raise UserError(_("Select invoice lines with a decided origin."))
        document = self._editable_document(lines)
        self._write_origin(
            lines, {"import_purchase_line_id": False, "import_origin_state": "pending"}
        )
        document.message_post(
            body=_("Origin of %(count)s line(s) undone.", count=len(lines))
        )
        return True

    def action_no_order(self):
        """Decide that the invoice lines have no order."""
        lines = self._split_selection()[0]
        if not lines:
            raise UserError(_("Select the invoice lines without an order."))
        document = self._editable_document(lines)
        self._write_origin(
            lines, {"import_purchase_line_id": False, "import_origin_state": "no_order"}
        )
        document.message_post(
            body=_(
                "%(count)s line(s) marked as without purchase order.", count=len(lines)
            )
        )
        return True

    def action_open_document(self):
        """Open the fiscal document of the selected note: for the fiscal group
        (the buyer decides the origin without reading the fiscal models)."""
        if not self.env.user.has_group("l10n_br_fiscal.group_user"):
            raise UserError(
                _(
                    "The fiscal document is for the fiscal profile. Ask someone "
                    "from the fiscal team to open it."
                )
            )
        document = self._split_selection()[0].document_id
        if len(document) != 1:
            raise UserError(_("Select the lines of one document."))
        return {
            "type": "ir.actions.act_window",
            "name": document.display_name,
            "res_model": "l10n_br_fiscal.document",
            "res_id": document.id,
            "view_mode": "form",
            "views": [(False, "form")],
        }

    def action_open_quote(self):
        """Open the quotation for the buyer to confirm it."""
        order = self._split_selection()[2].order_id
        if len(order) != 1:
            raise UserError(_("Select the lines of one quotation."))
        return {
            "type": "ir.actions.act_window",
            "name": order.name,
            "res_model": "purchase.order",
            "res_id": order.id,
            "view_mode": "form",
        }

    def action_create_order(self):
        """Create a draft purchase order with the invoice lines selected."""
        notes, orders, quotes = self._split_selection()
        if orders or quotes or not notes:
            raise UserError(_("Select only invoice lines to create the order."))
        document = self._editable_document(notes)
        self._check_units(notes)
        if not all(line.product_id for line in notes):
            raise UserError(_("Resolve the product of the selected lines first."))
        if notes.filtered(lambda line: line.import_origin_state == "resolved"):
            raise UserError(_("Undo the origin of the lines that already have one."))
        order = (
            self.env["purchase.order"]
            .with_company(document.company_id)
            .create(
                {
                    "partner_id": document.partner_id.id,
                    "company_id": document.company_id.id,
                    "origin": _("Fiscal document %s") % document.display_name,
                    "date_order": document.document_date or fields.Datetime.now(),
                    "order_line": [
                        fields.Command.create(self._prepare_order_line_vals(line))
                        for line in notes
                    ],
                }
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
    def _prepare_order_line_vals(self, line):
        """Quantity and price of the invoice line, in the unit of the product
        purchases."""
        product = line.product_id
        uom = product.uom_po_id or product.uom_id
        quantity, price = line.quantity, line.price_unit
        if line.uom_id and line.uom_id.category_id == uom.category_id:
            quantity = line.uom_id._compute_quantity(quantity, uom)
            price = line.uom_id._compute_price(price, uom)
        return {
            "product_id": product.id,
            "name": line.name,
            "product_qty": quantity,
            "product_uom": uom.id,
            "price_unit": price,
        }
