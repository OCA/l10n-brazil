# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE
#   Wagner Pereira <wagner.pereira@kmee.com.br>
# Copyright 2018 ABGF - Wagner Pereira <wagner.pereira@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _


class SituacaoGeradora(models.Model):
    _name = 'sped.situacao_geradora_acidente'
    _description = 'Situação Geradora do Acidente de Trabalho'
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

    @api.onchange('codigo')
    def _valida_codigo(self):
        for situacao in self:
            if situacao.codigo:
                if situacao.codigo.isdigit():
                    situacao.codigo = situacao.codigo.zfill(9)
                else:
                    res = {'warning': {
                        'title': _('Código Incorreto!'),
                        'message': _('Campo Código somente aceita números!'
                                     ' - Corrija antes de salvar')
                    }}
                    situacao.codigo = False
                    return res

    @api.depends('codigo', 'nome')
    def _compute_name(self):
        for situacao in self:
            situacao.name = situacao.codigo + '-' + situacao.nome
