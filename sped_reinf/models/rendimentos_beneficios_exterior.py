# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class RendimentosBeneficiosExterior(models.Model):

    _name = 'reinf.rendimentos_beneficios_exterior'
    _description = 'Forma de Tributação para rendimentos de beneficiários no Exterior'
    _sql_constraints = [
        ('codigo',
         'unique(codigo)',
         'Este código já existe !'
         )
    ]


    name = fields.Char()
    codigo = fields.Char(
        size=2,
        string='Código'
    )
    descricao = fields.Char(
        string='Descrição'
    )

    @api.onchange('codigo')
    def _valida_codigo(self):
        for codigop in self:
            if codigop.codigo:
                if codigop.codigo.isdigit():
                    codigop.codigo = codigop.codigo.zfill(9)
                else:
                    res = {'warning': {
                        'title': _('Código Incorreto!'),
                        'message': _(
                            'Campo Código somente aceita números! - Corrija antes de salvar')
                    }}
                    codigop.codigo = False
                    return res

    @api.depends('descricao', 'codigo')
    def _compute_name(self):
        for codigop in self:
            codigop.name = codigop.codigo + '-' + codigop.descricao

