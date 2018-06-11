# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE
#   Wagner Pereira <wagner.pereira@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _


class TipoLotacaoTributaria(models.Model):
    _name = 'sped.lotacao_tributaria'
    _description = 'Tipos de Lotação Tributária'
    _order = 'codigo'
    _rec_name = 'name'
    _sql_constraints = [
        ('codigo',
         'unique(codigo)',
         'Este código já existe !'
         )
    ]
    codigo = fields.Char(
        size=2,
        string='Codigo',
    )

    nome = fields.Text(
        string='Nome',
    )

    codigo_trabalhador_ids = fields.Many2many(
        string='Codigo',
        comodel_name='sped.categoria_trabalhador',
        relation='trabalhador_tributaria_ids',
    )

    codigo_tributaria_classificacao_ids = fields.Many2many(
        string='Codigo',
        comodel_name='sped.classificacao_tributaria',
        relation='tributaria_classificacao_ids',
    )

    descricao = fields.Char(
        string='Descrição',
        required=True,
    )
    preenchimento_campo = fields.Char(
        string=u'Preenchimento do campo {nrInsc}',
        required=True,
    )
    name = fields.Char(
        compute='_compute_name',
        store=True,
    )

    @api.onchange('codigo')
    def _valida_codigo(self):
        for lotacao in self:
            if lotacao.codigo:
                if lotacao.codigo.isdigit():
                    lotacao.codigo = lotacao.codigo.zfill(2)
                else:
                    res = {'warning': {
                        'title': _('Código Incorreto!'),
                        'message': _('Campo Código somente aceita números!'
                                     ' - Corrija antes de salvar')
                    }}
                    lotacao.codigo = False
                    return res

    @api.depends('codigo', 'descricao')
    def _compute_name(self):
        for lotacao in self:
            lotacao.name = lotacao.codigo

    @api.multi
    def name_get(self):
        result = []
        for s in self:
            result.append((s.id, s.name))
        return result
