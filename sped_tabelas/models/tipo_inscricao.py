# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE
#   Wagner Pereira <wagner.pereira@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import fields, models, api


class TipoInscricao(models.Model):
    _name = "sped.tipos_inscricao"
    _description = "Tipos de Inscrição"
    _order = 'codigo'

    codigo = fields.Integer(
        string='Codigo',
        required=True,
    )
    _sql_constraints = [
        ('codigo',
         'unique(codigo)',
         'Este código já existe !'
         )
    ]

    descricao = fields.Text(
        string='Nome',
        required=True,
    )

    name = fields.Char(
        compute='_compute_name',
        store=True,
    )

    @api.depends('codigo', 'descricao')
    def _compute_name(self):
        for tipo in self:
            tipo.name = str(tipo.codigo) + '-' + tipo.descricao
