# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


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
        help="Send Immediately: transmit the fiscal document to SEFAZ in the "
        "same transaction (synchronous).\n"
        "Send Later: enqueue the transmission as a queue_job, so the SEFAZ "
        "round trip does not block the user request.",
    )
