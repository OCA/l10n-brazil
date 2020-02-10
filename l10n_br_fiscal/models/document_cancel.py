# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class DocumentCancel(models.Model):
    _name = "l10n_br_fiscal.document.cancel"
    _description = "Documento Eletrônico no Sefaz"

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

    cancel_document_event_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document_event",
        inverse_name="cancel_document_event_id",
        string=u"Eventos",
    )

    display_name = fields.Char(string=u"Nome", compute="_compute_display_name")

    @api.multi
    @api.depends("document_id.number", "document_id.partner_id.name")
    def _compute_display_name(self):
        self.ensure_one()
        names = ["Fatura", self.document_id.number, self.document_id.partner_id.name]
        self.display_name = " / ".join(filter(None, names))

    @api.multi
    @api.constrains('justificative')
    def _check_justificative(self):
        for invalid in self:
            if len(invalid.justificative) < 15:
                return False
        return True
