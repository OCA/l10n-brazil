# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE
#   Wagner Pereira <wagner.pereira@kmee.com.br>
# Copyright 2018 ABGF - Wagner Pereira <wagner.pereira@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _


class Pais(models.Model):
    _name = 'sped.pais'
    _description = 'Países'
    _order = 'name'
    _sql_constraints = [
        ('codigo',
         'unique(codigo)',
         'Este código já existe !'
         )
    ]

    codigo = fields.Char(
        size=3,
        string='Codigo',
        required=True,
    )
    nome = fields.Char(
        string='Nome',
        required=True,
    )
    name = fields.Char(
        compute='_compute_name',
        store=True,
    )
    data_criacao = fields.Date(
        string='Data de Criação',
    )
    data_extincao = fields.Date(
        string='Data de Extinção',
    )

    @api.onchange('codigo')
    def _valida_codigo(self):
        for pais in self:
            if pais.codigo:
                if pais.codigo.isdigit():
                    pais.codigo = pais.codigo.zfill(3)
                else:
                    res = {'warning': {
                        'title': _('Código Incorreto!'),
                        'message': _('Campo Código somente aceita números!'
                                     ' - Corrija antes de salvar')
                    }}
                    pais.codigo = False
                    return res

    @api.depends('codigo', 'nome')
    def _compute_name(self):
        for pais in self:
            pais.name = pais.codigo + '-' + pais.nome
