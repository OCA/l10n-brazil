# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class DocumentCorrection(models.Model):
    _name = "l10n_br_fiscal.document.correction"
    _description = "Fiscal Document Correction Record"

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Documento",
        index=True,
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        related="document_id.partner_id",
        string="Partner",
        index=True,
    )

    company_id = fields.Many2one(
        comodel_name="res.partner",
        related="document_id.partner_id",
        string="Company",
        index=True,
    )

    justificative = fields.Char(
        string="Justificativa", size=255, readonly=True, required=True
    )

    sequence = fields.Char(
        string="Sequence",
        help="Indica a sequência da carta de correcão")

    cce_document_event_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.event",
        inverse_name="correction_document_event_id",
        string=u"Eventos",
    )

    display_name = fields.Char(
        string="Name",
        compute="_compute_display_name")

    @api.multi
    @api.depends("document_id.number", "document_id.partner_id")
    def _compute_display_name(self):
        self.ensure_one()
        names = ["Fatura", self.document_id.number,
                 self.document_id.partner_id.name]
        self.display_name = " / ".join(filter(None, names))
