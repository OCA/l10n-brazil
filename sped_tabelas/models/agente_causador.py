# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE
#   Wagner Pereira <wagner.pereira@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _


class AgenteCausador(models.Model):
    _name = 'sped.agente_causador'
    _description = 'Agente Causador do Acidente de Trabalho'
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
        for agente in self:
            if agente.codigo:
                if agente.codigo.isdigit():
                    agente.codigo = agente.codigo.zfill(9)
                else:
                    res = {'warning': {
                        'title': _('Código Incorreto!'),
                        'message': _('Campo Código somente aceita números! '
                                     '- Corrija antes de salvar')
                    }}
                    agente.codigo = False
                    return res

    @api.depends('codigo', 'nome')
    def _compute_name(self):
        for agente in self:
            agente.name = agente.codigo + '-' + agente.nome
