# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE
#   Wagner Pereira <wagner.pereira@kmee.com.br>
# Copyright 2018 ABGF - Wagner Pereira <wagner.pereira@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _


class ClassificacaoTributaria(models.Model):
    _name = 'sped.classificacao_tributaria'
    _description = 'Classificação Tributária'
    _order = 'codigo'
    _sql_constraints = [
        ('codigo',
         'unique(codigo)',
         'Este código já existe !'
         )
    ]
    codigo_tributaria_classificacao_ids = fields.Many2many(
        'sped.lotacao_tributaria',
        string='Codigo',
        relation='tributaria_classificacao_ids',
    )
    codigo_tributaria_fpas_ids = fields.Many2many(
        'sped.codigo_aliquota',
        string='Codigo',
        relation='tributaria_fpas_ids',
    )

    codigo = fields.Char(
        size=2,
        string='Código',
        required=True,
    )
    descricao = fields.Char(
        string='Classificação Tributária',
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
                    classificacao.codigo = classificacao.codigo.zfill(2)
                else:
                    res = {'warning': {
                        'title': _('Código Incorreto!'),
                        'message': _('Campo Código somente aceita números!'
                                     ' - Corrija antes de salvar')
                    }}
                    classificacao.codigo = False
                    return res

    @api.depends('codigo', 'descricao')
    def _compute_name(self):
        for classificacao in self:
            classificacao.name = classificacao.codigo
