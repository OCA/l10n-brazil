# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class FiscalOperation(models.Model):
    _inherit = "l10n_br_fiscal.operation"

    queue_document_send = fields.Selection(
        selection=[
            ("send_now", "Send Immediately"),
            ("with_delay", "Send Later"),
        ],
        string="Transmission moment",
        default="send_now",
        required=True,
    )
