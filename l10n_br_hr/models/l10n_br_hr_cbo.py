# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class L10nBrHrCbo(models.Model):
    _name = "l10n_br_hr.cbo"
    _description = "Brazilian Classification of Occupation"

    code = fields.Char(
        string='Code',
        required=True)

    name = fields.Char(
        string='Name',
        size=255,
        required=True,
        translate=True)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            result.append((record['id'], name))
        return result











