# Copyright (C) 2026  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import _, api, fields, models, tools
from odoo.osv import expression

_logger = logging.getLogger(__name__)

# Position of a purchase.order.line inside its order (the nItemPed semantic:
# 1-based position, NOT the sequence field which defaults to 10 for every
# interface-created line). Kept as a SQL fragment so the candidate view and
# the bill-matching reference derivation stay perfectly aligned.
PO_LINE_POSITION_SQL = """(
    SELECT COUNT(*) FROM purchase_order_line pol_pos
    WHERE pol_pos.order_id = {pol_alias}.order_id
      AND (pol_pos.sequence, pol_pos.id) <= ({pol_alias}.sequence, {pol_alias}.id)
)::int"""


class ImportMatchCandidate(models.Model):
    """Union view of the pre-existing documents an imported fiscal document
    line can be matched against: open purchase order lines and pending
    incoming picking moves of the document issuer.

    Document-type agnostic: shared by the NFe import wizard today and
    available to any other fiscal document importer (NFSe, CTe, utility
    bills...) inheriting the generic import wizard. For services (NFSe) the
    stock branch simply yields nothing while the purchase branch works for
    service lines as well.

    Ids encode the source: positive ids are ``purchase.order.line`` ids,
    negative ids are ``-stock.move`` ids (same trick as
    ``picking.bill.line.match``).

    Soft dependency: the SQL view is built only from the models actually
    installed (``purchase`` and/or ``stock``), so this module keeps no hard
    dependency on either. With neither installed the view is empty and the
    import wizards fall back to the plain product picker. The view is
    rebuilt in post_init_hook with the full registry (at module-graph time
    the optional models are not loaded yet).
    """

    _name = "l10n_br_fiscal.document.import.match.candidate"
    _description = "Fiscal Document Import Match Source Candidate"
    _auto = False
    _order = "source_type desc, ref_name, line_no"

    source_type = fields.Selection(
        selection=[
            ("stock_move", "Incoming Picking Line"),
            ("po_line", "Purchase Order Line"),
        ],
        readonly=True,
    )
    product_id = fields.Many2one(comodel_name="product.product", readonly=True)
    uom_id = fields.Many2one(comodel_name="uom.uom", readonly=True)
    qty = fields.Float(string="Open Quantity", readonly=True)
    price_unit = fields.Float(readonly=True)
    partner_id = fields.Many2one(comodel_name="res.partner", readonly=True)
    company_id = fields.Many2one(comodel_name="res.company", readonly=True)
    ref_name = fields.Char(string="Source Reference", readonly=True)
    line_no = fields.Integer(string="Line Position", readonly=True)
    # for moves linked to a PO: the PO name and the PO line position, i.e.
    # the canonical bill-matching key (xPed/nItemPed semantics):
    po_ref = fields.Char(string="Purchase Order", readonly=True)
    po_line_no = fields.Integer(string="PO Line Position", readonly=True)
    po_line_id = fields.Integer(
        readonly=True,
        help="purchase.order.line id: the line itself for po_line candidates, "
        "the linked PO line (purchase_line_id) for stock_move candidates. "
        "Used to collapse a PO line and its own receipt move into a single "
        "logical candidate.",
    )
    order_id = fields.Integer(readonly=True)
    picking_id = fields.Integer(readonly=True)

    @api.model
    def _register_hook(self):
        """Rebuild the SQL view once the FULL registry is loaded.

        init() runs with the module's own registry slice only, so the view
        may be built without the optional purchase/stock branches (their
        models load after l10n_br_fiscal_edi in the graph).
        _register_hook runs after the whole registry is ready — the Odoo 16
        equivalent of a post_init_hook that also fires on module updates
        (post_init_hook only runs on new installs there).
        """
        res = super()._register_hook()
        try:
            self.refresh_view()
        except Exception:
            _logger.exception("could not refresh the match candidate view")
        return res

    @property
    def _table_query(self):
        """Fallback definition used at install time (see post_init_hook).

        The view is built only from the models actually installed
        (``purchase`` and/or ``stock``). At module-graph time those models
        may not be in the registry yet, so this can degrade to the empty
        view; post_init_hook then rebuilds it with the full registry.
        """
        return " UNION ALL ".join(self._view_queries())

    def init(self):
        # Rebuild on every module install/update: the ORM runs init() for
        # _auto=False models with the module's own registry slice only, so
        # the view may still be built without the optional purchase/stock
        # branches here — post_init_hook (full registry) always fixes it
        # right after. The reverse order is what matters: init() guarantees
        # the view exists when l10n_br_fiscal_edi is merely updated, since
        # Odoo 16 only runs post_init_hook on new installs.
        self.refresh_view()

    @api.model
    def _view_queries(self):
        queries = []
        if self.env.get("stock.move") is not None:
            queries.append(self._select_stock_move())
        if self.env.get("purchase.order.line") is not None:
            queries.append(self._select_po_line())
        if not queries:
            queries.append(self._select_empty())
        return queries

    @api.model
    def refresh_view(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            # pylint: disable=sql-injection
            f"CREATE OR REPLACE VIEW {self._table} AS ({self._table_query})"
        )
        _logger.info("rebuilt SQL view %s", self._table)

    def _select_po_line(self):
        return f"""
            SELECT
                pol.id AS id,
                'po_line' AS source_type,
                pol.product_id AS product_id,
                pol.product_uom AS uom_id,
                pol.product_qty - pol.qty_invoiced AS qty,
                pol.price_unit AS price_unit,
                po.partner_id AS partner_id,
                po.company_id AS company_id,
                po.name AS ref_name,
                {PO_LINE_POSITION_SQL.format(pol_alias="pol")} AS line_no,
                po.name AS po_ref,
                {PO_LINE_POSITION_SQL.format(pol_alias="pol")} AS po_line_no,
                pol.id AS po_line_id,
                pol.order_id AS order_id,
                NULL::int AS picking_id
            FROM purchase_order_line pol
            JOIN purchase_order po ON po.id = pol.order_id
            WHERE po.state IN ('purchase', 'done')
              AND pol.product_id IS NOT NULL
              AND pol.product_qty > pol.qty_invoiced
        """

    def _select_stock_move(self):
        has_pol_link = self._stock_move_has_purchase_line()
        if has_pol_link:
            po_ref_sql = """(
                SELECT po2.name FROM purchase_order_line pol2
                JOIN purchase_order po2 ON po2.id = pol2.order_id
                WHERE pol2.id = sm.purchase_line_id
            )"""
            po_line_no_sql = f"""(
                SELECT {PO_LINE_POSITION_SQL.format(pol_alias="pol3")}
                FROM purchase_order_line pol3
                WHERE pol3.id = sm.purchase_line_id
            )"""
            po_line_id_sql = "sm.purchase_line_id"
            price_sql = """(
                SELECT pol4.price_unit FROM purchase_order_line pol4
                WHERE pol4.id = sm.purchase_line_id
            )"""
        else:
            po_ref_sql = "NULL::varchar"
            po_line_no_sql = "NULL::int"
            po_line_id_sql = "NULL::int"
            price_sql = "0.0"
        return f"""
            SELECT
                -sm.id AS id,
                'stock_move' AS source_type,
                sm.product_id AS product_id,
                sm.product_uom AS uom_id,
                sm.product_uom_qty - COALESCE(sm.quantity_done, 0) AS qty,
                {price_sql} AS price_unit,
                sp.partner_id AS partner_id,
                sm.company_id AS company_id,
                sp.name AS ref_name,
                (
                    SELECT COUNT(*) FROM stock_move sm_pos
                    WHERE sm_pos.picking_id = sm.picking_id
                      AND sm_pos.id <= sm.id
                )::int AS line_no,
                {po_ref_sql} AS po_ref,
                {po_line_no_sql} AS po_line_no,
                {po_line_id_sql} AS po_line_id,
                NULL::int AS order_id,
                sm.picking_id AS picking_id
            FROM stock_move sm
            JOIN stock_picking sp ON sp.id = sm.picking_id
            JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
            JOIN product_product pp ON pp.id = sm.product_id
            JOIN product_template ptmpl ON ptmpl.id = pp.product_tmpl_id
            WHERE spt.code = 'incoming'
              AND sm.state NOT IN ('done', 'cancel')
              AND sm.product_id IS NOT NULL
              AND ptmpl.type IN ('product', 'consu')
        """

    def _stock_move_has_purchase_line(self):
        """purchase_line_id is added to stock.move by purchase_stock only."""
        self.env.cr.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'stock_move' AND column_name = 'purchase_line_id'
            """
        )
        return bool(self.env.cr.fetchone())

    def _select_empty(self):
        return """
            SELECT
                0 AS id,
                NULL::varchar AS source_type,
                NULL::int AS product_id,
                NULL::int AS uom_id,
                0.0 AS qty,
                0.0 AS price_unit,
                NULL::int AS partner_id,
                NULL::int AS company_id,
                NULL::varchar AS ref_name,
                NULL::int AS line_no,
                NULL::varchar AS po_ref,
                NULL::int AS po_line_no,
                NULL::int AS po_line_id,
                NULL::int AS order_id,
                NULL::int AS picking_id
            WHERE false
        """

    def name_get(self):
        result = []
        for rec in self:
            product = rec.product_id
            code = f"[{product.default_code}] " if product.default_code else ""
            label = (
                f"{rec.ref_name} #{rec.line_no} - "
                f"{code}{product.name} - {rec.qty:g} {rec.uom_id.name}"
            )
            if rec.source_type == "po_line":
                label += f" @ {rec.price_unit}"
            elif rec.po_ref:
                label += f" (PO {rec.po_ref} #{rec.po_line_no})"
            result.append((rec.id, label))
        return result

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """Search by PO name, picking name, PO line reference or product.

        When the wizard passes the edited line's product in the context
        (``line_product_id``), the candidates for that product are flagged
        with a leading ``*`` and proposed first. The search is not
        restricted: any other candidate stays selectable, so an operator can
        always fix a wrong product mapping. The flag lives only in the
        suggestion list — ``name_get``/``display_name`` are untouched.
        """
        args = list(args or [])
        if name:
            domain = expression.OR(
                [
                    [("ref_name", operator, name)],
                    [("po_ref", operator, name)],
                    [("product_id", operator, name)],
                ]
            )
            args = expression.AND([args, domain])
        records = self.search(args, limit=limit)
        line_product_id = self.env.context.get("line_product_id")
        if not line_product_id:
            return records.name_get()
        matching = records.filtered(lambda r: r.product_id.id == line_product_id)
        matching_ids = set(matching.ids)
        records = matching + (records - matching)
        return [
            (rec_id, ("* " if rec_id in matching_ids else "") + label)
            for rec_id, label in records.name_get()
        ]

    def action_open_source(self):
        self.ensure_one()
        if self.source_type == "po_line" and self.env.get("purchase.order"):
            model, res_id = "purchase.order", self.order_id
        elif self.source_type == "stock_move" and self.env.get("stock.picking"):
            model, res_id = "stock.picking", self.picking_id
        else:
            return
        return {
            "name": _("Match Source"),
            "type": "ir.actions.act_window",
            "target": "new",
            "views": [[False, "form"]],
            "res_model": model,
            "res_id": res_id,
        }
