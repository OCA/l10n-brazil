# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    @api.depends("incoterm_id")
    def _compute_nfe40_modFrete(self):
        for record in self:
            if record.incoterm_id:
                record.nfe40_modFrete = record.incoterm_id.freight_responsibility
            else:
                record.nfe40_modFrete = "9"

    nfe40_modFrete = fields.Selection(
        compute=_compute_nfe40_modFrete,
        store=True,
    )

    nfe40_transporta = fields.Many2one(
        comodel_name="res.partner",
        related="carrier_id.partner_id",
        string="Dados do transportador",
    )
