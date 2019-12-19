# Copyright 2015 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    consulta_serasa = fields.One2many("consulta.serasa", "partner_id")

    @api.multi
    def do_consultar_serasa(self):
        for partner in self:
            vals = {"partner_id": partner.id, "data_consulta": datetime.now()}
            self.env["consulta.serasa"].create(vals)
        return True
