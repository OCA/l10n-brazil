# Copyright (C) 2025 Escodoo (https://www.escodoo.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.l10n_br_account_payment_order.constants import TIPO_SERVICO


class CNABPaymentRule(models.Model):
    """Rules to select CNAB Payment Way and Service Type based on conditions"""

    _name = "l10n_br_cnab.payment.rule"
    _description = "CNAB Payment Selection Rule"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)

    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
        ondelete="cascade",
        required=True,
    )

    match_bank_type = fields.Selection(
        [("same", "Same Bank"), ("other", "Other Bank"), ("any", "Any")],
        default="any",
        required=True,
    )
    match_partner_type = fields.Selection(
        [("employee", "Employee"), ("supplier", "Supplier"), ("any", "Any")],
        default="any",
        required=True,
    )

    payment_way_id = fields.Many2one(
        comodel_name="cnab.payment.way",
        required=True,
        domain="[('cnab_structure_id', '=', cnab_structure_id)]",
    )

    service_type = fields.Selection(
        selection=TIPO_SERVICO,
        required=True,
    )
