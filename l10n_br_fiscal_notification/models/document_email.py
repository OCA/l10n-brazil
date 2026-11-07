# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo
# Copyright 2020 - TODAY, Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER,
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_STATE_CANCEL,
)
from odoo.addons.l10n_br_fiscal_edi.constants.fiscal import (
    DOCUMENT_STATE_AUTHORIZED,
    DOCUMENT_STATE_DENIED,
)

NOTIFIED_STATE_FIELDS = {
    DOCUMENT_STATE_AUTHORIZED: "state_autorizada",
    DOCUMENT_STATE_CANCEL: "state_cancelada",
    DOCUMENT_STATE_DENIED: "state_denegada",
}


class DocumentEmail(models.Model):
    _name = "l10n_br_fiscal.document.email"
    _description = "Fiscal Document Email"

    name = fields.Char(
        readonly=True,
        store=True,
        copy=False,
        compute="_compute_name",
    )

    active = fields.Boolean(
        default=True,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
    )

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        string="Fiscal Document Type",
        help="Select the type of document that will be applied "
        "to the email templates definitions.",
    )

    issuer = fields.Selection(
        selection=DOCUMENT_ISSUER,
        default=DOCUMENT_ISSUER_COMPANY,
        required=True,
    )

    state_autorizada = fields.Boolean(
        string="Autorizada",
        help="Notify when the fiscal document is authorized.",
    )

    state_cancelada = fields.Boolean(
        string="Cancelada",
        help="Notify when the fiscal document is cancelled.",
    )

    state_denegada = fields.Boolean(
        string="Denegada",
        help="Notify when the fiscal document is denied.",
    )

    email_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Fiscal Document E-mail Template",
        required=True,
        domain=[("model", "=", "l10n_br_fiscal.document")],
        help="Select the email template that will be sent when "
        "this document state change.",
    )

    @api.depends(
        "document_type_id",
        "state_autorizada",
        "state_cancelada",
        "state_denegada",
    )
    def _compute_name(self):
        for record in self:
            document_type = record.document_type_id.name or _("Others Document Types")
            states = [
                record._fields[field_name].string
                for field_name in NOTIFIED_STATE_FIELDS.values()
                if record[field_name]
            ]
            if states:
                record.name = f"{document_type} - {', '.join(states)}"
            else:
                record.name = document_type
