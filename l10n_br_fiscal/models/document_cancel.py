# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DocumentCancel(models.Model):
    _name = "l10n_br_fiscal.document.cancel"
    _description = "Fiscal Document Cancel Record"

    justificative = fields.Char(
        string="Justificative",
        size=255,
        required=True)

    document_event_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.event",
        inverse_name="document_cancel_id",
        string="Events")

    display_name = fields.Char(
        string="Name",
        compute="_compute_display_name")

    @api.multi
    @api.depends("document_event_ids")
    def _compute_display_name(self):
        for record in self:
            if record.document_event_ids:
                # TODO
                record.display_name = record.document_event_ids[0].origin

    @api.multi
    @api.constrains("justificative")
    def _check_justificative(self):
        for record in self:
            if len(record.justificative) < 15:
                raise ValidationError(_(
                    "Justificativa deve ter tamanho mínimo de 15 caracteres."))
