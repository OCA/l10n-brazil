# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import models, fields, api


class SpedMunicipio(models.Model):
    _name = b'sped.municipio'
    _description = 'Municípios'
    _order = 'nome, estado'

    codigo_ibge = fields.Char(
        string='Código IBGE',
        size=11,
        required=True,
        index=True
    )
    codigo_siafi = fields.Char(
        string='Código SIAFI',
        size=5,
        index=True
    )
    codigo_anp = fields.Char(
        string='Código ANP',
        size=7
    )
    nome = fields.Char(
        string='Nome',
        size=80,
        required=True,
        index=True
    )
    estado_id = fields.Many2one(
        comodel_name='sped.estado',
        string='Estado',
        required=True,
        index=True
    )
    estado = fields.Char(
        string='Estado',
        related='estado_id.uf',
        store=True,
        index=True
    )
    pais_id = fields.Many2one(
        comodel_name='sped.pais',
        string='País',
        required=True,
        index=True
    )
    ddd = fields.Char(
        string='DDD',
        size=2
    )
    cep_unico = fields.Char(
        string='CEP único',
        size=9
    )

    _sql_constraints = [
        (
            'nome_estado_pais_unique',
            'unique (nome, estado_id, pais_id)',
            'O nome, estado e país não podem se repetir!',
        ),
    ]

    def name_get(self):
        res = []
        for municipio in self:
            nome = municipio.nome
            nome += ' - ' + municipio.estado

            if municipio.pais_id.iso_3166_alfa_2 != 'BR':
                if municipio.pais_id.nome != municipio.nome:
                    nome += ' - ' + municipio.pais_id.nome

            res.append((municipio.id, nome))

        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name and operator in ('=', 'ilike', '=ilike', 'like'):
            if operator != '=':
                name = name.strip().replace(' ', '%')

            if 'import_file' in self.env.context:
                args = [
                    '|',
                    ('codigo_ibge', '=', name),
                    '|',
                    ('nome', 'ilike', name),
                    ('estado', 'ilike', name),
                ] + args
            else:
                args = [
                    '|',
                    ('nome', 'ilike', name),
                    ('estado', 'ilike', name),
                ] + args

            municipios = self.search(args, limit=limit)
            return municipios.name_get()

        return super(SpedMunicipio, self).name_search(name=name, args=args,
                                                      operator=operator,
                                                      limit=limit)
