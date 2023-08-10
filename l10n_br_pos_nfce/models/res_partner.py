# Copyright (C) 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_anonymous_consumer = fields.Boolean(
        string="Is Anonymous Consumer",
        help="Indicates that the partner is an anonymous consumer",
    )

    def _compute_nfe40_ender(self):
        super(ResPartner, self)._compute_nfe40_ender()

        for rec in self.filtered("is_anonymous_consumer"):
            rec.nfe40_xLgr = ""
            rec.nfe40_nro = ""
            rec.nfe40_xCpl = ""
            rec.nfe40_xBairro = ""
            rec.nfe40_cMun = ""
            rec.nfe40_xMun = ""
            rec.nfe40_UF = ""
            rec.nfe40_cPais = ""
            rec.nfe40_xPais = ""
