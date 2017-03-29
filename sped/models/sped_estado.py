# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import models, fields, api


class Estado(models.Model):
    _name = 'sped.estado'
    _description = u'Estado'
    _rec_name = 'uf'
    _order = 'uf'
    _inherits = {'res.country.state': 'state_id'}

    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string=u'State original',
        ondelete='restrict',
        required=True
    )

    # def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
    # retorno = {}

    # for registro in self.browse(cursor, user_id, ids):
    # retorno[registro.id] = registro.uf + ' - ' + registro.nome

    # return retorno

    # def _procura_descricao(
    #   self, cursor, user_id, obj, nome_campo, args, context=None):
    # texto = args[0][2]

    # procura = [
    # '|', # Isto define o OR para os dois parâmetros seguintes
    # ('uf', '=', texto.upper()),
    # ('nome', 'ilike', texto),
    # ]
    # return procura

    uf = fields.Char(
        string=u'UF',
        size=2,
        required=True,
        index=True
    )
    nome = fields.Char(
        string=u'Nome',
        size=20,
        required=True,
        index=True
    )
    codigo_ibge = fields.Char(
        string=u'Código IBGE',
        size=2
    )
    fuso_horario = fields.Char(
        string=u'Fuso horário',
        size=20
    )
    pais_id = fields.Many2one(
        comodel_name='sped.pais',
        string=u'País'
    )

    _sql_constraints = [
        ('uf_unique', 'unique (uf)', u'A UF não pode se repetir!'),
        ('nome_unique', 'unique (nome)', u'O nome não pode se repetir!'),
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
            # if operator != '=':
            # name = name.strip().replace(' ', '%')

            if len(name) <= 2:
                args += ['|', ('uf', '=', name.upper()),
                         ('uf', 'ilike', name.upper())]
            else:
                args += ['|', ('uf', '=', name.upper()),
                         ('nome', 'ilike', name)]

        return super(Estado, self).name_search(
            name=name, args=args, operator=operator, limit=limit)
