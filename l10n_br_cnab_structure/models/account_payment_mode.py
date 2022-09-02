# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models


class AccountPaymentMode(models.Model):

    _inherit = "account.payment.mode"

    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
    )

    cnab_batch_id = fields.Many2one(
        comodel_name="l10n_br_cnab.batch",
        domain="[('cnab_structure_id', '=', cnab_structure_id)]",
    )

    cnab_payment_way_id = fields.Many2one(
        comodel_name="cnab.payment.way",
        string="Way of Payment",
        domain="[('cnab_structure_id', '=', cnab_structure_id)]",
    )
