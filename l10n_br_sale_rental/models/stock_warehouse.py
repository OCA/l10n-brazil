# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models

RENTAL_PICKING_TYPES = {
    # kind: (field, code, sequence code)
    "remessa": ("l10n_br_rental_out_type_id", "outgoing", "LOC-REM"),
    "retorno": ("l10n_br_rental_in_type_id", "incoming", "LOC-RET"),
}


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    l10n_br_rental_out_type_id = fields.Many2one(
        comodel_name="stock.picking.type", string="Rental Delivery Type"
    )
    l10n_br_rental_in_type_id = fields.Many2one(
        comodel_name="stock.picking.type", string="Rental Return Type"
    )

    def write(self, vals):
        res = super().write(vals)
        if vals.get("rental_allowed"):
            self._l10n_br_set_rental_rules()
        return res

    def _l10n_br_rental_picking_type(self, kind):
        """Picking type of the rental delivery (remessa) or return (retorno),
        created on the first use: sale_rental uses the regular delivery and
        receipt types, which carry the sale and purchase fiscal operations."""
        self.ensure_one()
        field_name, code, sequence_code = RENTAL_PICKING_TYPES[kind]
        if self[field_name]:
            return self[field_name]
        is_remessa = kind == "remessa"
        source = (
            self.rental_in_location_id if is_remessa else self.rental_out_location_id
        )
        destination = (
            self.rental_out_location_id if is_remessa else self.rental_in_location_id
        )
        picking_type = (
            self.env["stock.picking.type"]
            .sudo()
            .create(
                {
                    "name": _("Rental Delivery") if is_remessa else _("Rental Return"),
                    "code": code,
                    "sequence_code": sequence_code,
                    "warehouse_id": self.id,
                    "company_id": self.company_id.id,
                    "default_location_src_id": source.id,
                    "default_location_dest_id": destination.id,
                    "fiscal_operation_id": self.company_id._l10n_br_rental_operation(
                        kind
                    ).id,
                    "l10n_br_rental_kind": kind,
                }
            )
        )
        self[field_name] = picking_type
        return picking_type

    def _l10n_br_set_rental_rules(self):
        """Rental rules move the goods with their own picking types and fiscal
        operations: the pull rule (Rental In -> Rental Out) issues the remessa,
        the push rule (Rental Out -> Rental In) the retorno."""
        for warehouse in self.filtered("rental_allowed"):
            rules = self.env["stock.rule"].search(
                [
                    ("route_id", "=", warehouse.rental_route_id.id),
                    ("warehouse_id", "=", warehouse.id),
                ]
            )
            for rule in rules:
                if (
                    rule.action == "pull"
                    and rule.location_src_id == warehouse.rental_in_location_id
                ):
                    kind = "remessa"
                elif (
                    rule.action == "push"
                    and rule.location_src_id == warehouse.rental_out_location_id
                ):
                    kind = "retorno"
                else:
                    continue
                operation = warehouse.company_id._l10n_br_rental_operation(kind)
                rule.write(
                    {
                        "picking_type_id": warehouse._l10n_br_rental_picking_type(
                            kind
                        ).id,
                        "fiscal_operation_id": operation.id,
                        "invoice_state": "2binvoiced" if operation else "none",
                    }
                )
