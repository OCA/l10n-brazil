# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from openerp import models, fields, api


class Municipio(models.Model):
    _name = 'sped.municipio'
    _description = 'Município'
    _order = 'nome, estado'

    #def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        #retorno = {}

        #for registro in self.browse(cursor, user_id, ids):
            #retorno[registro.id] = ''

            #if registro.id != 0:
                #if registro.nome:
                    #retorno[registro.id] += registro.nome

                #if registro.estado_id:
                    #retorno[registro.id] += ' - ' + registro.estado_id.uf

                #if registro.pais_id and registro.pais_id.nome != 'Brasil':
                    #retorno[registro.id] += ' - ' + registro.pais_id.nome

                ##retorno[registro.id] += ' - ' + registro.codigo_ibge_formatado

        #return retorno

    #def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        #texto = args[0][2]

        #procura = [
            #'|',
            #('nome', 'ilike', texto),
            #('codigo_ibge', 'ilike', texto),
        #]

        #return procura

    #def _formata_codigo_ibge(self, codigo):
        #if codigo:
            #return codigo[:3] + '.' + codigo[3:6] + '-' + codigo[6] + '/' + codigo[7:]
        #else:
            #return ''

    #def _codigo_ibge_formatado(self, cursor, user_id, ids, fields, arg, context=None):
        #retorno = {}

        #for registro in self.browse(cursor, user_id, ids):
            #retorno[registro.id] = self._formata_codigo_ibge(registro.codigo_ibge)

        #return retorno

    codigo_ibge = fields.Char('Código IBGE', size=11, required=True, index=True)
    codigo_siafi = fields.Char('Código SIAFI', size=5, index=True)
    codigo_anp = fields.Char('Código ANP', size=7)
    nome = fields.NameChar('Nome', size=80, required=True, index=True)
    estado_id = fields.Many2one('sped.estado', 'Estado', required=True, index=True)
    estado = fields.UpperChar('Estado', related='estado_id.uf', store=True, index=True)
    pais_id = fields.Many2one('sped.pais', 'País', required=True, index=True)
    #descricao = fields.function(_descricao, string='Município', method=True, type='Char', fnct_search=_procura_descricao)
    #codigo_ibge_formatado = fields.function(_codigo_ibge_formatado, method=True, type='Char')
    ddd = fields.Char('DDD', size=2)
    cep_unico = fields.Char('CEP único', size=9)

    _sql_constraints = [
        ('codigo_ibge_unique', 'unique (codigo_ibge)', 'O código IBGE não pode se repetir!'),
        ('nome_estado_pais_unique', 'unique (nome, estado_id, pais_id)', 'O nome, estado e país não podem se repetir!'),
    ]

    @api.multi
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
    def name_search(self, name='', args=[], operator='ilike', limit=100):
        if name and operator in ('=', 'ilike', '=ilike', 'like'):
            if operator != '=':
                name = name.strip().replace(' ', '%')

            args += ['|', ('nome', 'ilike', name), ('estado', 'ilike', name)]

        return super(Municipio, self).name_search(name=name, args=args, operator=operator, limit=limit)
