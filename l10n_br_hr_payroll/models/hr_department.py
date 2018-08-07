# -*- coding: utf-8 -*-
# Copyright (C) 2018  Luiz Felipe do Divino - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, models, fields


class L10nBrHrDepartment(models.Model):
    _inherit = "hr.department"

    state = fields.Selection(
        selection=[
            ('ativo', 'Ativo'),
            ('inativo', 'Inativo'),
        ],
        string='Situação',
        default='ativo',
    )

    @api.multi
    def set_inativo(self):
        for record in self:
            for child in record.child_ids:
                child.set_inativo()
            else:
                record.state = 'inativo'
