# Copyright (C) 2020  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EventAbstract(models.AbstractModel):
    _name = "l10n_br_fiscal.event.abstract"
    _description = "Evento Abstrato"

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
        comodel_name="res.company",
        related="document_id.company_id",
        string="Company",
        index=True,
    )

    justificative = fields.Char(
        string="Justificativa", size=255, required=True
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
        if len(self.justificative) < 15:
            raise UserError(
                _('Justificativa deve ter tamanho minimo de 15 caracteres.'))
        return True
