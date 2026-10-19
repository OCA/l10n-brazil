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
        compute="_compute_nfe40_transporta",
        string="Dados do transportador",
    )

    @api.depends("carrier_id.partner_id", "nfe40_modFrete")
    def _compute_nfe40_transporta(self):
        """Carrier partner for the <transporta> group.

        NT 2021.004, rule X03-30 (rejection 845): with modFrete = 9 (no
        freight) the group <transporta> must not be informed.
        """
        for record in self:
            if record.nfe40_modFrete == "9":
                record.nfe40_transporta = False
            else:
                record.nfe40_transporta = record.carrier_id.partner_id

    total_weight = fields.Float(
        compute="_compute_total_weight",
        store=True,
        readonly=False,
    )

    @api.depends("nfe40_vol.nfe40_pesoB")
    def _compute_total_weight(self):
        """Total weight is the sum of the gross weight of the volumes.

        Without volumes the value already set (manually) is kept.
        """
        for record in self:
            if record.nfe40_vol:
                record.total_weight = sum(record.nfe40_vol.mapped("nfe40_pesoB"))
            else:
                record.total_weight = record.total_weight
