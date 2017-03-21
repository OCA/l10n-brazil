# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CNAE(models.Model):
    _description = u'CNAE'
    _name = 'sped.cnae'
    _order = 'codigo'
    _rec_name = 'cnae'

    @api.depends('codigo', 'descricao')
    def _cnae(self):
        for cnae in self:
            cnae.cnae = (
                cnae.codigo[:4] + '-' + cnae.codigo[4] + '/' + cnae.codigo[5:]
            )
            cnae.cnae += ' - ' + cnae.descricao

    codigo = fields.Char(
        string=u'Código',
        size=7,
        required=True,
        index=True,
    )
    descricao = fields.Char(
        string=u'Descrição',
        size=255,
        required=True,
        index=True,
    )
    cnae = fields.Char(
        string=u'CNAE',
        compute='_cnae',
        store=True,
    )

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name and operator in ('=', 'ilike', '=ilike', 'like'):
            if operator != '=':
                name = name.strip().replace(' ', '%')

            args += ['|', ('codigo', '=', name), ('descricao', 'ilike', name)]

        return super(CNAE, self).name_search(
            name=name, args=args, operator=operator, limit=limit)

    @api.depends('codigo')
    def _check_codigo(self):
        for cnae in self:
            if cnae.id:
                cnae_ids = self.search([
                    ('codigo', '=', cnae.codigo),
                    ('id', '!=', cnae.id)
                ])
            else:
                cnae_ids = self.search([('codigo', '=', cnae.codigo)])

            if len(cnae_ids) > 0:
                raise ValidationError(u'Código CNAE já existe na tabela!')
