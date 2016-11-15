# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from pybrasil.valor import valor_por_extenso_unidade
from pybrasil.valor.decimal import Decimal as D


TIPO_UNIDADE = (
    ('U', u'Unidade'),
    ('P', u'Peso'),
    ('V', u'Volume'),
    ('C', u'Comprimento'),
    ('A', u'Área'),
    ('T', u'Tempo'),
    ('E', u'Embalagem'),
)


class Unidade(models.Model):
    _description = 'Unidade de medida'
    #_inherits = {'product.uom': 'uom_id'}
    _name = 'sped.unidade'
    _order = 'codigo_unico'
    _rec_name = 'codigo'

    #uom_id = fields.Many2one('product.uom', 'UOM original', ondelete='restrict', required=True)

    TIPO_UNIDADE_UNIDADE = 'U'
    TIPO_UNIDADE_PESO = 'P'
    TIPO_UNIDADE_VOLUME = 'V'
    TIPO_UNIDADE_COMPRIMENTO = 'C'
    TIPO_UNIDADE_AREA = 'A'
    TIPO_UNIDADE_TEMPO = 'T'
    TIPO_UNIDADE_EMBALAGEM = 'E'

    tipo = fields.Selection(TIPO_UNIDADE, string=u'Tipo', required=True, index=True)
    codigo = fields.Char(string=u'Código', size=10, index=True)
    codigo_unico = fields.LowerChar(string=u'Código', size=10, index=True, compute='_codigo_unico', store=True)

    @api.one
    @api.depends('codigo')
    def _codigo_unico(self):
        self.codigo_unico = self.codigo.lower().strip().replace(' ', ' ').replace('²', '2').replace('³', '3') if self.codigo else False

    def _valida_codigo(self):
        valores = {}
        res = {'value': valores}

        if self.codigo:
            sql = u"""
            select
                u.id
            from
                sped_unidade u
            where
                lower(unaccent(u.codigo_unico)) = lower(unaccent('{codigo}'))
            """
            sql = sql.format(codigo=self.codigo.lower().strip().replace(' ', ' '))

            if self.id or self._origin.id:
                sql += u"""
                    and u.id != {id}
                """
                sql = sql.format(id=self.id or self._origin.id)

            self.env.cr.execute(sql)
            jah_existe = self.env.cr.fetchall()

            if jah_existe:
                raise ValidationError(u'Unidade de medida já existe!')

        return res

    @api.one
    @api.constrains('codigo')
    def constrains_codigo(self):
        self._valida_codigo()

    @api.onchange('codigo')
    def onchange_codigo(self):
        return self._valida_codigo()

    nome = fields.NameChar(string=u'Nome', size=60, index=True)
    nome_unico = fields.LowerChar(string=u'Nome', size=60, index=True, compute='_nome_unico', store=True)

    @api.one
    @api.depends('nome')
    def _nome_unico(self):
        self.nome_unico = self.nome.lower().strip().replace(' ', ' ') if self.nome else False

    def _valida_nome(self):
        valores = {}
        res = {'value': valores}

        if self.nome:
            sql = u"""
            select
                u.id
            from
                sped_unidade u
            where
                lower(unaccent(u.nome_unico)) = lower(unaccent('{nome}'))
            """
            sql = sql.format(nome=self.nome.lower().strip().replace(' ', ' '))

            if self.id or self._origin.id:
                sql += u"""
                    and u.id != {id}
                """
                sql = sql.format(id=self.id or self._origin.id)

            self.env.cr.execute(sql)
            jah_existe = self.env.cr.fetchall()

            if jah_existe:
                raise ValidationError(u'Nome da unidade de medida já existe!')

        return res

    @api.one
    @api.constrains('nome')
    def constrains_nome(self):
        self._valida_nome()

    @api.onchange('nome')
    def onchange_nome(self):
        return self._valida_nome()

    fator_relacao_decimal = fields.Float(u'Multiplica por', default=10, digits=(18, 6))
    precisao_decimal = fields.Float(u'Elevado a', default=2, digits=(18, 6))
    arredondamento = fields.Integer(u'Casas decimais para arredondamento', default=0)

    nome_singular = fields.LowerChar(string=u'Singular', size=60)
    nome_plural = fields.LowerChar(string=u'Plural', size=60)
    genero_masculino = fields.Boolean(string=u'Nome é masculino?', default=True)
    usa_meio = fields.Boolean(string=u'Usa meio?', default=False)
    usa_virgula = fields.Boolean(string=u'Usa vírgula?', default=True)
    subunidade_id = fields.Many2one('sped.unidade', string=u'Unidade decimal', ondelete='restrict')

    @api.one
    def extenso(self, numero=D(0)):
        parametros = {
            'numero': numero,
            'unidade': ('unidade', 'unidades'),
            'genero_unidade_masculino': False,
            'precisao_decimal': self.precisao_decimal,
            'unidade_decimal': ('subunidade', 'subunidades'),
            'genero_unidade_decimal_masculino': False,
            'mascara_negativo': ('menos %s', 'menos %s'),
            'fator_relacao_decimal': self.fator_relacao_decimal or 10,
            'usa_meio': self.usa_meio,
            'usa_fracao': False,
            'usa_virgula': self.usa_virgula,
        }

        if self.usa_virgula:
            parametros['fator_relacao_decimal'] = 10
            parametros['precisao_decimal'] = 2

        if self.nome_singular and self.nome_plural:
            parametros['unidade'] = (self.nome_singular, self.nome_plural)
            parametros['genero_unidade_masculino'] = self.genero_masculino

        if self.subunidade_id and self.subunidade_id.nome_singular and self.subunidade_id.nome_plural:
            parametros['unidade_decimal'] = (self.subunidade_id.nome_singular, self.subunidade_id.nome_plural)
            parametros['genero_unidade_decimal_masculino'] = self.subunidade_id.genero_masculino

        return valor_por_extenso_unidade(**parametros)

    @api.one
    @api.depends('nome_singular', 'nome_plural', 'genero_masculino', 'usa_meio', 'subunidade_id', 'usa_virgula', 'fator_relacao_decimal', 'precisao_decimal')
    def _extenso(self):
        parametros = {
            'numero': 0,
            'unidade': ('unidade', 'unidades'),
            'genero_unidade_masculino': False,
            'precisao_decimal': 0,
            'unidade_decimal': ('subunidade', 'subunidades'),
            'genero_unidade_decimal_masculino': False,
            'mascara_negativo': ('menos %s', 'menos %s'),
            'fator_relacao_decimal': self.fator_relacao_decimal or 10,
            'usa_meio': self.usa_meio,
            'usa_fracao': False,
            'usa_virgula': self.usa_virgula,
        }

        if self.nome_singular and self.nome_plural:
            parametros['unidade'] = (self.nome_singular, self.nome_plural)
            parametros['genero_unidade_masculino'] = self.genero_masculino

        if self.subunidade_id and self.subunidade_id.nome_singular and self.subunidade_id.nome_plural:
            parametros['unidade_decimal'] = (self.subunidade_id.nome_singular, self.subunidade_id.nome_plural)
            parametros['genero_unidade_decimal_masculino'] = self.subunidade_id.genero_masculino

        self.extenso_zero = valor_por_extenso_unidade(**parametros)
        parametros['numero'] = D('1')
        self.extenso_singular_inteiro = valor_por_extenso_unidade(**parametros)
        parametros['numero'] = D('1234567')
        self.extenso_plural_inteiro = valor_por_extenso_unidade(**parametros)

        parametros['precisao_decimal'] = self.precisao_decimal or 0

        if self.usa_virgula:
            parametros['fator_relacao_decimal'] = 10
            parametros['precisao_decimal'] = 2

        if self.usa_meio or self.subunidade_id or self.usa_virgula:
            parametros['numero'] = D('1.5')
            self.extenso_singular_meio = valor_por_extenso_unidade(**parametros)
        else:
            self.extenso_singular_meio = self.extenso_singular_inteiro

        if self.subunidade_id or self.usa_virgula:
            parametros['numero'] = D('1.01')
            self.extenso_singular_um_decimo = valor_por_extenso_unidade(**parametros)
            parametros['numero'] = D('1.67')
            self.extenso_singular_decimal = valor_por_extenso_unidade(**parametros)
            parametros['numero'] = D('1234567.89')
            self.extenso_plural_decimal = valor_por_extenso_unidade(**parametros)
        else:
            self.extenso_singular_um_decimo = self.extenso_singular_inteiro
            self.extenso_singular_decimal = self.extenso_singular_inteiro
            self.extenso_plural_decimal = self.extenso_plural_inteiro

    extenso_zero = fields.Char(string=u'Ex. 0', compute=_extenso)
    extenso_singular_inteiro = fields.Char(string=u'Ex. 1', compute=_extenso)
    extenso_plural_inteiro = fields.Char(string=u'Ex. 1.234.567', compute=_extenso)

    extenso_singular_um_decimo = fields.Char(string=u'Ex. 1,01', compute=_extenso)
    extenso_singular_meio = fields.Char(string=u'Ex. 1,50', compute=_extenso)
    extenso_singular_decimal = fields.Char(string=u'Ex. 1,67', compute=_extenso)
    extenso_plural_decimal = fields.Char(string=u'Ex. 1.234.567,89', compute=_extenso)

    _sql_constraints = [
        ('codigo_unique', 'unique(codigo_unico)', u'Código da unidade de medida não pode se repetir'),
        ('nome_unique', 'unique(nome_unico)', u'Nome da unidade de medida não pode se repetir'),
    ]

    @api.model
    def name_search(self, name='', args=[], operator='ilike', limit=100):
        if name and operator in ('=', 'ilike', '=ilike', 'like'):
            #if operator != '=':
                #name = name.strip().replace(' ', '%')

            name = name.replace('²', '2')
            name = name.replace('³', '3')

            args += [['codigo_unico', 'ilike', name]]

        print(name, args)

        return super(Unidade, self).name_search(name=name, args=args, operator=operator, limit=limit)
