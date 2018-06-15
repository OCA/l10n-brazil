# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE
#   Wagner Pereira <wagner.pereira@kmee.com.br>
# Copyright 2018 ABGF - Wagner Pereira <wagner.pereira@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models


class TipoBeneficio(models.Model):
    _name = 'sped.tipo_beneficio'
    _description = 'Tipos de Benefícios Previdenciários' \
                   ' dos Regimes Próprios de Previdência'
    _order = 'codigo'
    _sql_constraints = [
        ('codigo',
         'unique(codigo)',
         'Este código já existe !'
         )
    ]

    codigo = fields.Integer(
        string='Codigo',
        required=True,
    )
    nome = fields.Char(
        string='Nome',
        required=True,
    )
    descricao = fields.Text(
        string='Descrição',
    )
    name = fields.Char(
        compute='_compute_name',
        store=True,
    )

    @api.depends('codigo', 'nome')
    def _compute_name(self):
        for tipo in self:
            tipo.name = str(tipo.codigo) + '-' + tipo.nome
