# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

RENTAL_OPERATIONS = {
    "rental": ("rental_fiscal_operation_id", "l10n_br_fiscal.fo_locacao"),
    "remessa": (
        "rental_remessa_fiscal_operation_id",
        "l10n_br_fiscal.fo_remessa_comodato",
    ),
    "retorno": (
        "rental_retorno_fiscal_operation_id",
        "l10n_br_fiscal.fo_entrada_retorno_comodato",
    ),
}


class ResCompany(models.Model):
    _inherit = "res.company"

    rental_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Rental Fiscal Operation",
        domain=[("fiscal_operation_type", "=", "out"), ("state", "=", "approved")],
        help="Rental charge (rental service lines). Empty: Locação de bens móveis.",
    )
    rental_remessa_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Rental Delivery Fiscal Operation",
        domain=[("fiscal_operation_type", "=", "out"), ("state", "=", "approved")],
        help="Goods leaving to the lessee. Empty: Remessa em comodato/locação.",
    )
    rental_retorno_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Rental Return Fiscal Operation",
        domain=[("fiscal_operation_type", "=", "in"), ("state", "=", "approved")],
        help="Goods coming back from the lessee."
        " Empty: Entrada de retorno de comodato/locação.",
    )

    def _l10n_br_rental_operation(self, kind):
        self.ensure_one()
        field_name, xmlid = RENTAL_OPERATIONS[kind]
        return self[field_name] or self.env.ref(xmlid, raise_if_not_found=False)
