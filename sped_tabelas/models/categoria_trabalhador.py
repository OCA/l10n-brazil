# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE
#   Wagner Pereira <wagner.pereira@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _

CATEGORIA_GRUPO = (
    ('1', 'Empregado e Trabalhador Temporário'),
    ('2', 'Avulso'),
    ('3', 'Agente Público'),
    ('4', 'Cessão'),
    ('7', 'Contribuinte Individual'),
    ('9', 'Bolsista'),
)


class CategoriaTrabalhador(models.Model):
    _name = 'sped.categoria_trabalhador'
    _description = 'Categorias de Trabalhadores'
    _order = 'name'
    _sql_constraints = [
        ('codigo',
         'unique(codigo)',
         'Este código já existe !'
         )
    ]

    codigo_tributaria_ids = fields.Many2many(
        string='Codigo',
        comodel_name='sped.lotacao_tributaria',
        relation='trabalhador_tributaria_ids',
    )

    codigo = fields.Char(
        size=3,
        string='Codigo',
        required=True,
    )
    nome = fields.Char(
        string='Nome',
        required=True,
    )
    classificacao_tributaria = fields.Text(
        string='Classificação Tributária'
    )
    descricao = fields.Text(
        string='Descrição',
    )
    grupo = fields.Selection(
        string='Grupo',
        selection=CATEGORIA_GRUPO,
        default='1',
        required=True,
    )
    name = fields.Char(
        compute='_compute_name',
        store=True,
    )

    @api.onchange('codigo')
    def _valida_codigo(self):
        for categoria in self:
            if categoria.codigo:
                if categoria.codigo.isdigit():
                    categoria.codigo = categoria.codigo.zfill(3)
                else:
                    res = {'warning': {
                        'title': _('Código Incorreto!'),
                        'message': _('Campo Código somente aceita números!'
                                     ' - Corrija antes de salvar')
                    }}
                    categoria.codigo = False
                    return res

    @api.depends('codigo', 'nome')
    def _compute_name(self):
        for categoria in self:
            categoria.name = categoria.codigo + '-' + categoria.nome
