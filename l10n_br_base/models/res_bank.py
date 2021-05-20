#    Copyright (C) 2016 MultidadosTI (http://www.multidadosti.com.br)
#    @author Michell Stuttgart <michellstut@gmail.com>
#    Copyright (C) 2021 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.osv import expression


class ResBank(models.Model):
    _inherit = "res.bank"
    _order = "code_bc, name"

    short_name = fields.Char(
        string="Short Name",
    )

    code_bc = fields.Char(
        string="Brazilian Bank Code",
        size=3,
        help="Brazilian Bank Code ex.: 001 is the code of Banco do Brasil",
    )

    ispb_number = fields.Char(
        string="ISPB Number",
        size=8,
    )

    compe_member = fields.Boolean(
        string="COMPE Member",
        default=False,
    )

    @api.multi
    def name_get(self):
        name_template = super().name_get()
        name_dict = dict([(x[0], x[1]) for x in name_template])

        result = []
        for br_template in self:
            if br_template.code_bc:
                name = '[{}] {}'.format(
                    br_template.code_bc,
                    name_dict[br_template.id]
                )
            else:
                name = name_dict[br_template.id]
            result.append([br_template.id, name])
        return result

    @api.model
    def _name_search(
            self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|',
                      ('code_bc', '=ilike', name + '%'),
                      '|',
                      ('bic', '=ilike', name + '%'),
                      ('name', operator, name)
                      ]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&'] + domain
        bank_ids = self._search(
            domain + args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(bank_ids).name_get()
