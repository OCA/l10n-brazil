# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class CodigoPagamento(models.Model):

    _name = 'codigo.pagamento'
    _description = 'Codigo Pagamento'
    _sql_constraints = [
        ('codigo',
         'unique(codigo)',
         'Este código já existe !'
         )
    ]


    name = fields.Char()
    classificacao_rendimento = fields.Selection(
        selection=[('brasil', 'Beneficiários no Brasil'),
                   ('rra', 'Beneficiários no Brasil e Justiça – RRA '),
                   ('exterior', 'Remessa Exterior')],
        string='Classificação do rendimento'
    )
    cod_rendimento = fields.Char(
        size=4,
        string='Código de Rendimento'
    )
    descricao = fields.Char(
        string='Descrição'
    )
    beneficiario_pj = fields.Boolean(
        string='Beneficiário PJ'
    )
    beneficiario_pf = fields.Boolean(
        string='Beneficiário PF'
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

    @api.depends('codigo', 'nome')
    def _compute_name(self):
        for codigop in self:
            codigop.name = codigop.codigo + '-' + codigop.nome

