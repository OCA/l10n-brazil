# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SpedCNAE(models.Model):
    _name = b'sped.cnae'
    _description = 'CNAEs'
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
        string='Código',
        size=7,
        required=True,
        index=True,
    )
    descricao = fields.Char(
        string='Descrição',
        size=255,
        required=True,
        index=True,
    )
    cnae = fields.Char(
        string='CNAE',
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
            cnaes = self.search(args, limit=limit)
            return cnaes.name_get()

        return super(SpedCNAE, self).name_search(name=name, args=args,
                                             operator=operator, limit=limit)

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
                raise ValidationError(_(u'Código CNAE já existe na tabela!'))
