# @ 2021 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models

# Position of a purchase.order.line inside its order (the nItemPed semantic:
# 1-based position, NOT the sequence field which defaults to 10 for every
# interface-created line). Twin of the expression used by the NFe import
# match candidate view in l10n_br_nfe — keep them aligned.
_PO_LINE_POSITION_SQL = """(
    SELECT COUNT(*) FROM purchase_order_line pol_pos
    WHERE pol_pos.order_id = {pol_alias}.order_id
      AND (pol_pos.sequence, pol_pos.id) <= ({pol_alias}.sequence, {pol_alias}.id)
)::int"""


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_price_unit_invoice(self, inv_type, partner, qty=1):
        result = super()._get_price_unit_invoice(inv_type, partner, qty)
        # Caso tenha Purchase Line já vem desagrupado aqui devido ao KEY
        if len(self) == 1:
            # Caso venha apenas uma linha porem sem
            # purchase_line_id é preciso ignora-la
            if self.purchase_line_id and self.purchase_line_id.price_unit != result:
                result = self.purchase_line_id.price_unit

        return result

    @api.model
    def _get_bill_matching_reference_sql(self, alias):
        """Duck-typing hook picked up dynamically by `stock_picking_bill_matching`.
        The `alias` argument (e.g., 'aml' or 'sm') is passed by the SQL view builder.

        The explicit (partner_order, partner_order_line) reference (xPed /
        nItemPed semantics) is used when present, normalized like the
        account.move.line side in l10n_br_account. When absent — the common
        case, as xPed is optional in the NFe layout and the fields must be
        filled before the PO is confirmed — the reference falls back to the
        canonical key derived from the linked purchase order line:
        (PO name, 1-based line position), which is exactly the key the NFe
        import wizard synthesizes on the bill side when the operator matches
        a source reference. Both sides then reconcile without any supplier
        cooperation. Truncated to the fiscal field sizes (Char(15)/Char(6))
        to match what the ORM stores on the bill side.
        """
        item = (
            f"COALESCE(NULLIF(REGEXP_REPLACE("
            f"BTRIM(LEFT(COALESCE({alias}.partner_order_line, ''), 6)), "
            f"'[^0-9]', '', 'g'), '')::int::varchar, "
            f"NULLIF(BTRIM(LEFT(COALESCE({alias}.partner_order_line, ''), 6)), ''), "
            f"'')"
        )
        explicit_ref = (
            f"NULLIF(BTRIM(LEFT(COALESCE({alias}.partner_order, ''), 15)) "
            f"|| '-' || {item}, '-')"
        )
        po_derived_ref = (
            "(SELECT LEFT(po_ref.name, 15) || '-' || "
            + _PO_LINE_POSITION_SQL.format(pol_alias="pol_ref")
            + "::varchar"
            " FROM purchase_order_line pol_ref"
            " JOIN purchase_order po_ref ON po_ref.id = pol_ref.order_id"
            f" WHERE pol_ref.id = {alias}.purchase_line_id)"
        )
        return f"COALESCE({explicit_ref}, {po_derived_ref})"
