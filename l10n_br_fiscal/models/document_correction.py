# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class DocumentCorrection(models.Model):
    _name = "l10n_br_fiscal.document.correction"
    _description = "Fiscal Document Correction Record"

    motivo = fields.Text(
        string="Reason Description",
        readonly=True,
        required=True)

    sequence = fields.Char(
        string="Sequence",
        help="Indica a sequência da carta de correcão")

    document_event_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.event",
        inverse_name="document_correction_id",
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
