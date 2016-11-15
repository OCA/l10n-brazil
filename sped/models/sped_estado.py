# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from openerp import models, fields, api


class Estado(models.Model):
    _name = 'sped.estado'
    _description = 'Estado'
    _rec_name = 'uf'
    _order = 'uf'
    _inherits = {'res.country.state': 'state_id'}

    state_id = fields.Many2one('res.country.state', 'State original', ondelete='restrict', required=True)

    #def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        #retorno = {}

        #for registro in self.browse(cursor, user_id, ids):
            #retorno[registro.id] = registro.uf + ' - ' + registro.nome

        #return retorno

    #def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        #texto = args[0][2]

        #procura = [
            #'|', # Isto define o OR para os dois parâmetros seguintes
            #('uf', '=', texto.upper()),
            #('nome', 'ilike', texto),
            #]
        #return procura

    uf = fields.UpperChar('UF', size=2, required=True, index=True)
    nome = fields.NameChar('Nome', size=20, required=True, index=True)
    codigo_ibge = fields.Char('Código IBGE', size=2)
    fuso_horario = fields.Char('Fuso horário', size=20)
    pais_id = fields.Many2one('sped.pais', string='País')

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
    def name_search(self, name='', args=[], operator='ilike', limit=100):
        print(args, operator)
        if name and operator in ('=', 'ilike', '=ilike', 'like'):
            name = name.strip()
            #if operator != '=':
                #name = name.strip().replace(' ', '%')

            if len(name) <= 2:
                args += ['|', ('uf', '=', name.upper()), ('uf', 'ilike', name.upper())]
            else:
                args += ['|', ('uf', '=', name.upper()), ('nome', 'ilike', name)]

        print(args)

        return super(Estado, self).name_search(name=name, args=args, operator=operator, limit=limit)
