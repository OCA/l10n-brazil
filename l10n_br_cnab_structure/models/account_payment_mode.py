from odoo import _, api, fields, models


class AccountPaymentMode(models.Model):

    _inherit = "account.payment.mode"

    cnab_file_id = fields.Many2one(
        comodel_name="l10n_br_cnab.file",
    )

    cnab_batch_id = fields.Many2one(
        comodel_name="l10n_br_cnab.batch",
        domain="[('cnab_file_id', '=', cnab_file_id)]",
    )
