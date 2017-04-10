# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import models, fields, api


class Municipio(models.Model):
    _name = 'sped.municipio'
    _description = u'Município'
    _order = 'nome, estado'

    codigo_ibge = fields.Char(
        string=u'Código IBGE',
        size=11,
        required=True,
        index=True
    )
    codigo_siafi = fields.Char(
        string=u'Código SIAFI',
        size=5,
        index=True
    )
    codigo_anp = fields.Char(
        string=u'Código ANP',
        size=7
    )
    nome = fields.Char(
        string=u'Nome',
        size=80,
        required=True,
        index=True
    )
    estado_id = fields.Many2one(
        comodel_name='sped.estado',
        string=u'Estado',
        required=True,
        index=True
    )
    estado = fields.Char(
        string=u'Estado',
        related='estado_id.uf',
        store=True,
        index=True
    )
    pais_id = fields.Many2one(
        comodel_name='sped.pais',
        string=u'País',
        required=True,
        index=True
    )
    ddd = fields.Char(
        string=u'DDD',
        size=2
    )
    cep_unico = fields.Char(
        string=u'CEP único',
        size=9
    )

    _sql_constraints = [
        (
            'nome_estado_pais_unique',
            'unique (nome, estado_id, pais_id)',
            u'O nome, estado e país não podem se repetir!',
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

            args += ['|', ('nome', 'ilike', name), ('estado', 'ilike', name)]

        return super(Municipio, self).name_search(
            name=name, args=args, operator=operator, limit=limit)
