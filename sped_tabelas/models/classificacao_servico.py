# -*- coding: utf-8 -*-
#
# Copyright 2018 KMEE
#   Wagner Pereira <wagner.pereira@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _


class ClassificacaoServico(models.Model):
    _name = 'sped.classificacao_servico'
    _description = 'Classificação de Serviços Prestados mediante cessão de mão de obra/Empreitada'
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
        for classificacao in self:
            if classificacao.codigo:
                if classificacao.codigo.isdigit():
                    classificacao.codigo = agente.codigo.zfill(9)
                else:
                    res = {'warning': {
                        'title': _('Código Incorreto!'),
                        'message': _('Campo Código somente aceita números! '
                                     '- Corrija antes de salvar')
                    }}
                    classificacao.codigo = False
                    return res

    @api.depends('codigo', 'nome')
    def _compute_name(self):
        for classificacao in self:
            classificacao.name = classificacao.codigo + '-' + classificacao.nome
