# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from openerp import models, fields, api


class SpedEstado(models.Model):
    _name = b'sped.estado'
    _description = 'Estados'
    _rec_name = 'uf'
    _order = 'uf'
    _inherits = {'res.country.state': 'state_id'}

    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='State original',
        ondelete='restrict',
        required=True
    )

    uf = fields.Char(
        string='UF',
        size=2,
        required=True,
        index=True
    )
    nome = fields.Char(
        string='Nome',
        size=20,
        required=True,
        index=True
    )
    codigo_ibge = fields.Char(
        string='Código IBGE',
        size=2
    )
    fuso_horario = fields.Char(
        string='Fuso horário',
        size=20
    )
    pais_id = fields.Many2one(
        comodel_name='sped.pais',
        string='País'
    )

    _sql_constraints = [
        ('uf_unique', 'unique (uf)', 'A UF não pode se repetir!'),
        ('nome_unique', 'unique (nome)', 'O nome não pode se repetir!'),
    ]

    @api.multi
    def name_get(self):
        res = []
        for estado in self:
            nome = estado.uf
            nome += ' - ' + estado.nome
            res.append((estado.id, nome))

        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name and operator in ('=', 'ilike', '=ilike', 'like'):
            name = name.strip()

            if len(name) <= 2:
                args += ['|', ('uf', '=', name.upper()),
                         ('uf', 'ilike', name.upper())]
            else:
                args += ['|', ('uf', '=', name.upper()),
                         ('nome', 'ilike', name)]

            estados = self.search(args, limit=limit)
            return estados.name_get()

        return super(SpedEstado, self).name_search(name=name, args=args,
                                               operator=operator, limit=limit)
