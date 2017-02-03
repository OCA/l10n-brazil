# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import api, fields, models
from odoo.exceptions import ValidationError
from ..constante_tributaria import (
    TIPO_UNIDADE,
)

import json
import logging

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor import valor_por_extenso_unidade
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)


class Unidade(models.Model):
    _description = u'Unidade de medida'
    _inherits = {'product.uom': 'uom_id'}
    _name = 'sped.unidade'
    _order = 'codigo_unico'
    _rec_name = 'codigo'

    TIPO_UNIDADE_UNIDADE = 'U'
    TIPO_UNIDADE_PESO = 'P'
    TIPO_UNIDADE_VOLUME = 'V'
    TIPO_UNIDADE_COMPRIMENTO = 'C'
    TIPO_UNIDADE_AREA = 'A'
    TIPO_UNIDADE_TEMPO = 'T'
    TIPO_UNIDADE_EMBALAGEM = 'E'

    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string=u'UOM original',
        ondelete='restrict',
        required=True,
    )
    tipo = fields.Selection(
        selection=TIPO_UNIDADE,
        string=u'Tipo',
        required=True,
        index=True,
    )
    codigo = fields.Char(
        string=u'Código',
        size=10,
        index=True,
    )
    codigo_unico = fields.Char(
        string=u'Código',
        size=10,
        index=True,
        # compute='_compute_codigo_unico',
        store=True
    )
    nome = fields.Char(
        string=u'Nome',
        size=60,
        index=True,
    )
    nome_unico = fields.Char(
        string=u'Nome',
        size=60,
        index=True,
        # compute='_compute_nome_unico',
        store=True,
    )
    #
    # Valores nas unidades por extenso
    #
    fator_relacao_decimal = fields.Float(
        string=u'Multiplica por',
        default=10,
        digits=(18, 6),
    )
    precisao_decimal = fields.Float(
        string=u'Elevado a',
        default=2,
        digits=(18, 6),
    )
    arredondamento = fields.Integer(
        string=u'Casas decimais para arredondamento',
        default=0,
    )
    nome_singular = fields.Char(
        string=u'Singular',
        size=60,
    )
    nome_plural = fields.Char(
        string=u'Plural',
        size=60,
    )
    genero_masculino = fields.Boolean(
        string=u'Nome é masculino?',
        default=True,
    )
    usa_meio = fields.Boolean(
        string=u'Usa meio?',
        default=False,
    )
    usa_virgula = fields.Boolean(
        string=u'Usa vírgula?',
        default=True,
    )
    subunidade_id = fields.Many2one(
        comodel_name='sped.unidade',
        string=u'Unidade decimal',
        ondelete='restrict',
    )
    #
    # Campos para usar a unidade com o campo Monetary
    #
    symbol = fields.Char('Symbol', size=11, compute='_compute_symbol')
    position = fields.Char('Position', compute='_compute_symbol')
    rounding = fields.Float(string='Rounding Factor', digits=(12, 6),
                            default=0.01, compute='_compute_symbol')
    decimal_places = fields.Integer(compute='_compute_symbol')
    active = fields.Boolean(compute='_compute_symbol')

    #
    # Exemplos do texto por extenso
    #
    extenso_zero = fields.Char(
        string=u'Ex. 0',
        compute='_compute_extenso',
    )
    extenso_singular_inteiro = fields.Char(
        string=u'Ex. 1',
        compute='_compute_extenso',
    )
    extenso_plural_inteiro = fields.Char(
        string=u'Ex. 1.234.567',
        compute='_compute_extenso',
    )
    extenso_singular_um_decimo = fields.Char(
        string=u'Ex. 1,01',
        compute='_compute_extenso',
    )
    extenso_singular_meio = fields.Char(
        string=u'Ex. 1,50',
        compute='_compute_extenso',
    )
    extenso_singular_decimal = fields.Char(
        string=u'Ex. 1,67',
        compute='_compute_extenso',
    )
    extenso_plural_decimal = fields.Char(
        string=u'Ex. 1.234.567,89',
        compute='_compute_extenso',
    )

    # @api.depends('codigo')
    # def _compute_codigo_unico(self):
    #     for unidade in self:
    #         codigo_unico = unidade.codigo or ''
    #         codigo_unico = codigo_unico.lower().strip()
    #         codigo_unico = codigo_unico.replace(' ', ' ')
    #         codigo_unico = codigo_unico.replace('²', '2')
    #         codigo_unico = codigo_unico.replace('³', '3')
    #         unidade.codigo_unico = codigo_unico

    # @api.depends('nome')
    # def _compute_nome_unico(self):
    #     for unidade in self:
    #         nome_unico = unidade.nome or ''
    #         nome_unico = nome_unico.lower().strip()
    #         # nome_unico = nome_unico.replace(' ', ' ')
    #         nome_unico = nome_unico.replace('²', '2')
    #         nome_unico = nome_unico.replace('³', '3')
    #         unidade.nome_unico = nome_unico

    @api.depends('codigo')
    def _check_codigo(self):
        for unidade in self:
            if unidade.id:
                unidade_ids = self.search([
                    ('codigo_unico', '=', unidade.codigo_unico),
                    ('id', '!=', unidade.id)
                ])
            else:
                unidade_ids = self.search([
                    ('codigo_unico', '=', unidade.codigo_unico)
                ])

            if len(unidade_ids) > 0:
                raise ValidationError(u'Código de unidade já existe!')

    @api.depends('nome')
    def _check_nome(self):
        for unidade in self:
            if unidade.id:
                unidade_ids = self.search(
                    [('nome_unico', '=', unidade.nome_unico),
                     ('id', '!=', unidade.id)])
            else:
                unidade_ids = self.search(
                    [('nome_unico', '=', unidade.nome_unico)])

            if len(unidade_ids) > 0:
                raise ValidationError(u'Nome de unidade já existe!')

    @api.multi
    def extenso(self, numero=D(0)):
        self.ensure_one()

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

        if (self.subunidade_id and
                self.subunidade_id.nome_singular and
                self.subunidade_id.nome_plural):
            parametros['unidade_decimal'] = (
                self.subunidade_id.nome_singular,
                self.subunidade_id.nome_plural
            )
            parametros['genero_unidade_decimal_masculino'] = (
                self.subunidade_id.genero_masculino
            )

        return valor_por_extenso_unidade(**parametros)

    @api.depends(
        'nome_singular',
        'nome_plural',
        'genero_masculino',
        'usa_meio',
        'subunidade_id',
        'usa_virgula',
        'fator_relacao_decimal',
        'precisao_decimal')
    def _compute_extenso(self):
        for unidade in self:
            parametros = {
                'numero': 0,
                'unidade': ('unidade', 'unidades'),
                'genero_unidade_masculino': False,
                'precisao_decimal': 0,
                'unidade_decimal': ('subunidade', 'subunidades'),
                'genero_unidade_decimal_masculino': False,
                'mascara_negativo': ('menos %s', 'menos %s'),
                'fator_relacao_decimal': unidade.fator_relacao_decimal or 10,
                'usa_meio': unidade.usa_meio,
                'usa_fracao': False,
                'usa_virgula': unidade.usa_virgula,
            }

            if unidade.nome_singular and unidade.nome_plural:
                parametros['unidade'] = (
                    unidade.nome_singular, unidade.nome_plural)
                parametros[
                    'genero_unidade_masculino'] = unidade.genero_masculino

            if (unidade.subunidade_id and
                    unidade.subunidade_id.nome_singular and
                    unidade.subunidade_id.nome_plural):
                parametros['unidade_decimal'] = (
                    unidade.subunidade_id.nome_singular,
                    unidade.subunidade_id.nome_plural)
                parametros['genero_unidade_decimal_masculino'] = (
                    unidade.subunidade_id.genero_masculino
                )

            unidade.extenso_zero = valor_por_extenso_unidade(**parametros)
            parametros['numero'] = D('1')
            unidade.extenso_singular_inteiro = valor_por_extenso_unidade(
                **parametros)
            parametros['numero'] = D('1234567')
            unidade.extenso_plural_inteiro = valor_por_extenso_unidade(
                **parametros)

            parametros['precisao_decimal'] = unidade.precisao_decimal or 0

            if unidade.usa_virgula:
                parametros['fator_relacao_decimal'] = 10
                parametros['precisao_decimal'] = 2

            if (unidade.usa_meio or
                    unidade.subunidade_id or
                    unidade.usa_virgula):
                parametros['numero'] = D('1.5')
                unidade.extenso_singular_meio = valor_por_extenso_unidade(
                    **parametros
                )
            else:
                unidade.extenso_singular_meio = (
                    unidade.extenso_singular_inteiro
                )

            if unidade.subunidade_id or unidade.usa_virgula:
                parametros['numero'] = D('1.01')
                unidade.extenso_singular_um_decimo = valor_por_extenso_unidade(
                    **parametros)
                parametros['numero'] = D('1.67')
                unidade.extenso_singular_decimal = valor_por_extenso_unidade(
                    **parametros)
                parametros['numero'] = D('1234567.89')
                unidade.extenso_plural_decimal = valor_por_extenso_unidade(
                    **parametros)
            else:
                unidade.extenso_singular_um_decimo = (
                    unidade.extenso_singular_inteiro
                )
                unidade.extenso_singular_decimal = (
                    unidade.extenso_singular_inteiro
                )
                unidade.extenso_plural_decimal = (
                    unidade.extenso_plural_inteiro
                )

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            name = name.replace(' ', ' ')
            name = name.replace('²', '2')
            name = name.replace('³', '3')
            args += ['|', ['codigo_unico', operator, name],
                     ['nome_unico', operator, name]]

        return super(Unidade, self).name_search(name=name, args=args,
                                                operator=operator, limit=limit)

    def prepare_sync_to_uom(self):
        self.ensure_one()

        if (self.tipo == self.TIPO_UNIDADE_UNIDADE or
                self.tipo == self.TIPO_UNIDADE_EMBALAGEM):
            category_id = self.env.ref('product.product_uom_categ_unit').id

        elif self.tipo == self.TIPO_UNIDADE_PESO:
            category_id = self.env.ref('product.product_uom_categ_kgm').id

        elif self.tipo == self.TIPO_UNIDADE_VOLUME:
            category_id = self.env.ref('product.product_uom_categ_vol').id

        elif self.tipo == self.TIPO_UNIDADE_COMPRIMENTO:
            category_id = self.env.ref('product.uom_categ_length').id

        elif self.tipo == self.TIPO_UNIDADE_AREA:
            category_id = self.env.ref('sped.product_uom_categ_area').id

        elif self.tipo == self.TIPO_UNIDADE_TEMPO:
            category_id = self.env.ref('product.uom_categ_wtime').id

        dados = {
            'name': self.codigo,
            'category_id': category_id,
            'active': True,
            'sped_unidade_id': self.id,
        }

        if not self.uom_id:
            dados['uom_type'] = 'bigger'
            dados['factor'] = 1
            dados['rounding'] = 0.01

        return dados

    @api.multi
    def sync_to_uom(self):
        for unidade in self:
            dados = unidade.prepare_sync_to_uom()
            unidade.uom_id.write(dados)

    @api.model
    def create(self, dados):
        dados['name'] = dados['codigo']

        if dados['tipo'] == self.TIPO_UNIDADE_UNIDADE or dados[
                'tipo'] == self.TIPO_UNIDADE_EMBALAGEM:
            dados['category_id'] = self.env.ref(
                'product.product_uom_categ_unit').id

        elif dados['tipo'] == self.TIPO_UNIDADE_PESO:
            dados['category_id'] = self.env.ref(
                'product.product_uom_categ_kgm').id

        elif dados['tipo'] == self.TIPO_UNIDADE_VOLUME:
            dados['category_id'] = self.env.ref(
                'product.product_uom_categ_vol').id

        elif dados['tipo'] == self.TIPO_UNIDADE_COMPRIMENTO:
            dados['category_id'] = self.env.ref('product.uom_categ_length').id

        elif dados['tipo'] == self.TIPO_UNIDADE_AREA:
            dados['category_id'] = self.env.ref(
                'sped.product_uom_categ_area').id

        elif dados['tipo'] == self.TIPO_UNIDADE_TEMPO:
            dados['category_id'] = self.env.ref('product.uom_categ_wtime').id

        unidade = super(Unidade, self).create(dados)
        unidade.sync_to_uom()

        return unidade

    @api.multi
    def write(self, dados):
        if 'codigo' in dados:
            dados['name'] = dados['codigo']

        res = super(Unidade, self).write(dados)
        self.sync_to_uom()
        return res

    #
    # Para uso com o field.Monetary
    #
    @api.depends('codigo')
    def _compute_symbol(self):
        for unidade in self:
            self.active = True
            self.position = 'after'
            self.symbol = ' ' + self.codigo

            if (self.tipo == self.TIPO_UNIDADE_UNIDADE or
                    self.tipo == self.TIPO_UNIDADE_EMBALAGEM):
                self.decimal_places = 0
            else:
                self.decimal_places = len(
                    str(int(self.fator_relacao_decimal * (
                        10 ** self.precisao_decimal))))

            self.rounding = D(10) ** (self.decimal_places * -1)

    @api.model
    def get_format_currencies_js_function(self):
        """ Returns a string that can be used to instanciate a javascript
        function that formats numbers as currencies.
            That function expects the number as first parameter and
        the currency id as second parameter.
            If the currency id parameter is false or undefined,
        the company currency is used.
        """
        function = ""
        for unidade in self.search([]):
            symbol = unidade.codigo
            format_number_str = "openerp.web.format_value(arguments[0], " \
                                "{type: 'float', digits: [69,%s]}, 0.00)" \
                                % self.decimal_places
            return_str = "return %s + '\\xA0' + %s;" % (
                json.dumps(symbol), format_number_str)
            function += "if (arguments[1] === %s) { %s }" % (
                unidade.id, return_str)
            if unidade == self.env.ref('sped.UNIDADE_UNIDADE'):
                company_currency_format = return_str
        function = "if (" \
                   "arguments[1] === false || arguments[1] === undefined" \
                   ") {" + company_currency_format + " }" + function

        return function

    @api.multi
    def round(self, amount):
        # self.ensure_one()
        amount = D(amount or 0)
        if (self.tipo == self.TIPO_UNIDADE_UNIDADE or
                self.tipo == self.TIPO_UNIDADE_EMBALAGEM):
            return amount.quantize(D(1))
        amount = amount.quantize(D(10) * D(self.decimal_places * -1))
        return amount
