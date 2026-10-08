# Copyright (C) 2023 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    nfce_document_serie_id = fields.Many2one(
        string="Document Serie",
        comodel_name="l10n_br_fiscal.document.serie",
    )

    nfce_environment = fields.Selection(
        string="Environment",
        related="company_id.nfe_environment",
        store=True,
        readonly=True,
    )

    nfce_document_serie_code = fields.Char(
        string="Document Serie Code",
        related="nfce_document_serie_id.code",
        readonly=True,
    )

    nfce_city_ibge_code = fields.Char(
        related="company_id.city_id.ibge_code",
    )
