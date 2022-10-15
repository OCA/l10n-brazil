# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from odoo.addons.l10n_br_base.models.res_partner_pix import PartnerPix


class CNABPixKeyType(models.Model):
    """CNAB Pix Key Type"""

    _name = "cnab.pix.key.type"
    _description = "CNAB Pix Key Type"

    name = fields.Char(compute="_compute_name")
    code = fields.Char(required=True)
    description = fields.Char()

    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
        string="Cnab Structure",
        ondelete="cascade",
        required=True,
    )

    key_type = fields.Selection(
        selection=PartnerPix.KEY_TYPES,
        string="PIX Key Type",
        required=True,
    )

    @api.depends("code", "name")
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.code} - {rec.description}"
