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
