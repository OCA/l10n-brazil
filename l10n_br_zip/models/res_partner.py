# Copyright (C) 2020  Gabriel Cardoso de Faria - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api

class Partner(models.Model):
    _inherit = "res.partner"

    @api.onchange("zip")
    def _onchange_zip(self):
        res = super()._onchange_zip() or {}
        try:
            zip_search = self.zip_search()
            res.update(zip_search)
        except Exception as e:
            pass
        return res
