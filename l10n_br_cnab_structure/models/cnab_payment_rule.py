# Copyright (C) 2025 Escodoo (https://www.escodoo.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

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

    @api.model
    def _find_matching_rule(self, cnab_structure, partner, partner_bank, journal):
        """Finds the first rule of the structure that matches bank and partner."""
        if partner_bank.bank_id == journal.bank_id:
            bank_type = "same"
        else:
            bank_type = "other"
        if getattr(partner, "employee", False):
            partner_type = "employee"
        else:
            partner_type = "supplier"
        rules = self.search([("cnab_structure_id", "=", cnab_structure.id)])
        for rule in rules:
            if rule.match_bank_type not in ("any", bank_type):
                continue
            if rule.match_partner_type not in ("any", partner_type):
                continue
            return rule
        return self.browse()
