# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import models, fields, api
from odoo.exceptions import ValidationError


class NaturezaOperacao(models.Model):
    _name = 'sped.natureza.operacao'
    _description = u'Naturezas de operação fiscal'
    _rec_name = 'nome'
    _order = 'nome'

    codigo = fields.Char(
        string=u'Código',
        size=10,
        required=True,
        index=True,
    )
    codigo_unico = fields.Char(
        string=u'Código',
        size=10,
        index=True,
        compute='_compute_codigo_unico',
        store=True,
    )
    nome = fields.Char(
        string=u'Nome',
        size=60,
        required=True,
        index=True,
    )
    nome_unico = fields.Char(
        string=u'Nome',
        size=60,
        index=True,
        compute='_compute_nome_unico',
        store=True,
    )

    @api.depends('codigo')
    def _compute_codigo_unico(self):
        for natureza_operacao in self:
            codigo_unico = natureza_operacao.codigo or ''
            codigo_unico = codigo_unico.lower().strip()
            codigo_unico = codigo_unico.replace(' ', ' ')
            natureza_operacao.codigo_unico = codigo_unico

    @api.depends('nome')
    def _compute_nome_unico(self):
        for natureza_operacao in self:
            nome_unico = natureza_operacao.nome or ''
            nome_unico = nome_unico.lower().strip()
            nome_unico = nome_unico.replace(' ', ' ')
            natureza_operacao.nome_unico = nome_unico

    @api.depends('codigo')
    def _check_codigo(self):
        for natureza_operacao in self:
            if natureza_operacao.id:
                natureza_operacao_ids = self.search([
                    ('codigo_unico', '=', natureza_operacao.codigo_unico)
                    ('id', '!=', natureza_operacao.id)
                ])
            else:
                natureza_operacao_ids = natureza_operacao.search([
                    ('codigo_unico', '=', natureza_operacao.codigo_unico)
                ])

            if len(natureza_operacao_ids) > 0:
                raise ValidationError(
                    u'Código de natureza de operação fiscal já existe!'
                )

    @api.depends('nome')
    def _check_nome(self):
        for natureza_operacao in self:
            if natureza_operacao.id:
                natureza_operacao_ids = self.search([
                    ('nome_unico', '=', natureza_operacao.nome_unico),
                    ('id', '!=', natureza_operacao.id)
                ])
            else:
                natureza_operacao_ids = natureza_operacao.search([
                    ('nome_unico', '=', natureza_operacao.nome_unico)
                ])

            if len(natureza_operacao_ids) > 0:
                raise ValidationError(
                    u'Natureza de operação fiscal já existe!'
                )
