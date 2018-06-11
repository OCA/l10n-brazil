# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE
#   Wagner Pereira <wagner.pereira@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _


class NaturezaLesao(models.Model):
    _name = 'sped.natureza_lesao'
    _description = 'Descrição da Natureza da Lesão'
    _order = 'name'
    _sql_constraints = [
        ('codigo',
         'unique(codigo)',
         'Este código já existe !'
         )
    ]

    codigo = fields.Char(
        size=9,
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
    descricao = fields.Text(
        string='Descrição',
    )

    @api.onchange('codigo')
    def _valida_codigo(self):
        for natureza in self:
            if natureza.codigo:
                if natureza.codigo.isdigit():
                    natureza.codigo = natureza.codigo.zfill(9)
                else:
                    res = {'warning': {
                        'title': _('Código Incorreto!'),
                        'message': _('Campo Código somente aceita números!'
                                     ' - Corrija antes de salvar')
                    }}
                    natureza.codigo = False
                    return res

    @api.depends('codigo', 'nome')
    def _compute_name(self):
        for natureza in self:
            natureza.name = natureza.codigo + '-' + natureza.nome
