# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BeneficiosRendimentosExterior(models.Model):

    _name = 'reinf.beneficio_rendimento_exterior'
    _description = 'Rendimentos de Beneficiários no Exterior'
    _sql_constraints = [
        ('codigo',
         'unique(codigo)',
         'Este código já existe !'
         )
    ]

    name = fields.Char()
    codigo = fields.Char(
        size=3,
        string='Código'
    )
    descricao = fields.Char(
        string='Descrição'
    )

    @api.onchange('codigo')
    def _valida_codigo(self):
        for beneficio_exterior in self:
            if beneficio_exterior.codigo:
                if beneficio_exterior.codigo.isdigit():
                    beneficio_exterior.codigo = beneficio_exterior.codigo.zfill(3)
                else:
                    res = {'warning': {
                        'title': _('Código Incorreto!'),
                        'message': _(
                            'Campo Código somente aceita números! - Corrija antes de salvar')
                    }}
                    beneficio_exterior.codigo = False
                    return res

    @api.depends('descricao', 'codigo')
    def _compute_name(self):
        for beneficio_exterior in self:
            beneficio_exterior.name = beneficio_exterior.codigo + '-' + beneficio_exterior.descricao

