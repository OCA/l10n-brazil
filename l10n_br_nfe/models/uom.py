# Copyright 2019 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class Uom(models.Model):
    _inherit = 'uom.uom'

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict,
                            create_m2o=False, model=None):
        "if uom not found, break hard, don't create it"
        if rec_dict.get('name'):
            # TODO FIXME where are the BR unit names supposed to live?
            BR2ODOO = {'UN': 'Unit(s)', 'LU': 'Liter(s)'}
            name = BR2ODOO.get(rec_dict['name'], rec_dict['name'])
            domain = [('name', '=', name)]
            match = self.search(domain, limit=1)
            if match:
                return match.id
        return False
