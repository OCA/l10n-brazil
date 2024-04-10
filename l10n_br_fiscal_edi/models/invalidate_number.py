# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class InvalidateNumber(models.Model):
    _inherit = "l10n_br_fiscal.invalidate.number"

    event_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.event",
        inverse_name="invalidate_number_id",
        string="Events",
        readonly=True,
        states={"done": [("readonly", True)]},
    )

    # Authorization Event Related Fields
    authorization_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.event",
        string="Authorization Event",
        readonly=True,
        copy=False,
    )

    authorization_date = fields.Datetime(
        string="Authorization Date",
        readonly=True,
        related="authorization_event_id.protocol_date",
    )

    authorization_protocol = fields.Char(
        string="Authorization Protocol",
        related="authorization_event_id.protocol_number",
        readonly=True,
    )

    send_file_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="authorization_event_id.file_request_id",
        string="Send Document File XML",
        ondelete="restrict",
        readonly=True,
    )

    authorization_file_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="authorization_event_id.file_response_id",
        string="Authorization File XML",
        ondelete="restrict",
        readonly=True,
    )
