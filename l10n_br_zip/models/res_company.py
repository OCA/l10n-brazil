# Copyright (C) 2020  Gabriel Cardoso de Faria - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api

class Company(models.Model):
    _inherit = "res.company"

    @api.onchange("zip")
    def _onchange_zip(self):
        super()._onchange_zip()
        return self.zip_search()
