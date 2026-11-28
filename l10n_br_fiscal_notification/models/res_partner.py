# Copyright (C) 2021  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    edoc_send_email = fields.Boolean(
        string="Send Fiscal Documents by E-mail",
        tracking=True,
        help="Receive by e-mail the fiscal documents issued to this partner, "
        "with the authorization XML and the DANFE attached. Enable it on the "
        "contacts that should be notified, the company itself or any of its "
        "child contacts.",
    )
