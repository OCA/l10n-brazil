# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE
#   Wagner Pereira <wagner.pereira@kmee.com.br>
# Copyright 2018 ABGF - Wagner Pereira <wagner.pereira@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _


class FinanciamentoAposentadoria(models.Model):
    _name = 'sped.financiamento_aposentadoria'
    _description = 'Financiamento da Aposentadoria Especial e Redução' \
                   'do Tempo de Contribuição'
    _order = 'name'
    _sql_constraints = [
        ('codigo',
         'unique(codigo)',
         'Este código já existe !'
         )
    ]

    codigo = fields.Char(
        size=1,
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
        for financiamento in self:
            if financiamento.codigo:
                if financiamento.codigo.isdigit():
                    financiamento.codigo = financiamento.codigo.zfill(1)
                else:
                    res = {'warning': {
                        'title': _('Código Incorreto!'),
                        'message': _('Campo Código somente aceita números!'
                                     ' - Corrija antes de salvar')
                    }}
                    financiamento.codigo = False
                    return res

    @api.depends('codigo', 'nome')
    def _compute_name(self):
        for financiamento in self:
            financiamento.name = financiamento.codigo + '-' + \
                                 financiamento.nome
