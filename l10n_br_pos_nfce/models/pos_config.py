# Copyright (C) 2023 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    nfce_document_serie_id = fields.Many2one(
        string="Document Serie",
        comodel_name="l10n_br_fiscal.document.serie",
        related="company_id.nfe_default_serie_id",
    )

    nfce_environment = fields.Selection(
        string="Environment",
        related="company_id.nfe_environment",
        store=True,
        readonly=True,
    )

    nfce_document_serie_code = fields.Char(
        string="Document Serie Code",
        related="company_id.nfe_default_serie_id.code",
        readonly=True,
    )

    nfce_document_serie_sequence_number_next = fields.Integer(
        string="Document Serie Number",
        default=lambda self: self._default_next_number(),
    )

    nfce_city_ibge_code = fields.Char(
        related="company_id.city_id.ibge_code",
    )

    def _default_next_number(self):
        if not self.nfce_document_serie_id:
            return 1

        return self.nfce_document_serie_id.internal_sequence_id.number_next_actual

    def update_nfce_serie_number(self, serie_number):
        if self.nfce_document_serie_sequence_number_next < serie_number:
            self.nfce_document_serie_sequence_number_next = serie_number

        return self.nfce_document_serie_sequence_number_next
