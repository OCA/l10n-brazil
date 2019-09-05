# -*- coding: utf-8 -*-
# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class HrContract(models.Model):
    _name = 'hr.contract.category'
    _order = 'code'
    _description = 'Categoria de Contrato'

    _sql_constraints = [
        ('codigo_unico',
         'unique(code)',
         'O código da categoria não pode ser duplicado!'
         )
    ]

    name = fields.Char(
        string=u'Nome',
        compute='_compute_name',
        store=True,
    )
    code = fields.Char(
        string=u'Código',
        required=True,
    )
    description = fields.Char(
        string=u'Descrição',
        required='True',
    )

    @api.multi
    @api.depends('code', 'description')
    def _compute_name(self):
        for record in self:
            record.name = '%s - %s' % (record.code, record.description)
