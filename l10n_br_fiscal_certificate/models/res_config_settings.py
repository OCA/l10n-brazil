# Copyright (C) 2015  Luis Felipe Miléo - KMEE <mileo@kmee.com.br>
# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cert_expired_alert = fields.Integer(
        string="Certificate Expired Alert",
        config_parameter="l10n_br_fiscal_cert_expired_alert",
        required=True,
        default=30,
    )
