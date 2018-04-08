# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# Copyright (C) 2018 KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from __future__ import division, print_function, unicode_literals
from odoo import models, fields, api


class L10nBrBaseCity(models.Model):
    """ Este objeto persite todos os municípios relacionado a um estado.
    No Brasil é necesário em alguns documentos fiscais informar o código
    do IBGE dos município envolvidos na transação.
    """
    _name = b'l10n_br_base.city'
    _description = u'record'

    name = fields.Char(
        string='name',
        size=64,
        required=True
    )
    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Estado',
        required=True
    )
    country_id = fields.Many2one(
        related='state_id.country_id',
        store=True,
        string="Pais"
    )
    ibge_code = fields.Char(
        string=u'Código IBGE',
        size=7
    )
    siafi_code = fields.Char(
        string='Código SIAFI',
        size=5,
        index=True
    )
    anp_code = fields.Char(
        string='Código ANP',
        size=7
    )
    uf = fields.Char(
        string='Estado',
        related='state_id.code',
        store=True,
        index=True
    )
    phone_code = fields.Char(
        string='DDD',
        size=2
    )
    cep_unico = fields.Char(
        string='CEP único',
        size=9,
    )

    _sql_constraints = [
        (
            'name_estado_pais_unique',
            'unique (name, state_id, country_id)',
            'O nome, estado e país não podem se repetir!',
        ),
    ]

    def name_get(self):
        res = []
        for record in self:
            name = record.name
            name += ' - ' + record.uf

            if record.country_id.code != 'BR':
                if record.country_id.name != record.name:
                    name += ' - ' + record.country_id.name

            res.append((record.id, name))

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
                    ('ibge_code', '=', name),
                    '|',
                    ('name', 'ilike', name),
                    ('uf', 'ilike', name),
                ] + args
            else:
                args = [
                    '|',
                    ('name', 'ilike', name),
                    ('uf', 'ilike', name),
                ] + args

            records = self.search(args, limit=limit)
            return records.name_get()

        return super(L10nBrBaseCity, self).name_search(
            name=name, args=args, operator=operator, limit=limit)
