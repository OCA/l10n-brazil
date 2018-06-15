# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE
#   Wagner Pereira <wagner.pereira@kmee.com.br>
# Copyright 2018 ABGF - Wagner Pereira <wagner.pereira@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _


class FatoresRiscoMeioAmbiente(models.Model):
    _name = 'sped.fatores_meio_ambiente'
    _description = 'Fatores de Risco do Meio Ambiente do Trabalho'
    _order = 'name'
    _sql_constraints = [
        ('codigo',
         'unique(codigo)',
         'Este código já existe')
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
        for elemento in self:
            cod_novo = limpa_formatacao(elemento.codigo)
            if not cod_novo.isdigit():
                res = {'warning': {
                    'title': _('Código Incorreto!'),
                    'message': _('Campo Código somente aceita '
                                 'números ou pontos!'
                                 ' - Corrija antes de salvar')
                }}
                return res

    @api.depends('codigo', 'nome')
    def _compute_name(self):
        for c in self:
            c.name = c.codigo + '-' + c.nome


def limpa_formatacao(codigo):
    codigof = ''
    for d in codigo:
        if d != '.':
            codigof += d
    return codigof
