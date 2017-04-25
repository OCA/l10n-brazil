# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from ..constante_tributaria import TIPO_UNIDADE

import logging

_logger = logging.getLogger(__name__)

try:
    from pybrasil.base import tira_acentos
    from pybrasil.valor import valor_por_extenso_unidade
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedUnidade(models.Model):
    _name = b'sped.unidade'
    _description = 'Unidade de medida'
    _inherits = {'product.uom': 'uom_id'}
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
        string='UOM original',
        ondelete='restrict',
        required=True,
    )
    tipo = fields.Selection(
        selection=TIPO_UNIDADE,
        string='Tipo',
        required=True,
        index=True,
    )
    codigo = fields.Char(
        string='Código',
        size=10,
        index=True,
    )
    codigo_unico = fields.Char(
        string='Código',
        size=10,
        index=True,
        compute='_compute_codigo_unico',
        store=True
    )
    nome = fields.Char(
        string='Nome',
        size=60,
        index=True,
    )
    nome_unico = fields.Char(
        string='Nome',
        size=60,
        index=True,
        compute='_compute_nome_unico',
        store=True,
    )
    #
    # Valores nas unidades por extenso
    #
    fator_relacao_decimal = fields.Float(
        string='Multiplica por',
        default=10,
        digits=(18, 6),
    )
    precisao_decimal = fields.Float(
        string='Elevado a',
        default=2,
        digits=(18, 6),
    )
    arredondamento = fields.Integer(
        string='Casas decimais para arredondamento',
        default=0,
    )
    nome_singular = fields.Char(
        string='Singular',
        size=60,
    )
    nome_plural = fields.Char(
        string='Plural',
        size=60,
    )
    genero_masculino = fields.Boolean(
        string='Nome é masculino?',
        default=True,
    )
    usa_meio = fields.Boolean(
        string='Usa meio?',
        default=False,
    )
    usa_virgula = fields.Boolean(
        string='Usa vírgula?',
        default=True,
    )
    subunidade_id = fields.Many2one(
        comodel_name='sped.unidade',
        string='Unidade decimal',
        ondelete='restrict',
    )

    #
    # Exemplos do texto por extenso
    #
    extenso_zero = fields.Char(
        string='Ex. 0',
        compute='_compute_extenso',
    )
    extenso_singular_inteiro = fields.Char(
        string='Ex. 1',
        compute='_compute_extenso',
    )
    extenso_plural_inteiro = fields.Char(
        string='Ex. 1.234.567',
        compute='_compute_extenso',
    )
    extenso_singular_um_decimo = fields.Char(
        string='Ex. 1,01',
        compute='_compute_extenso',
    )
    extenso_singular_meio = fields.Char(
        string='Ex. 1,50',
        compute='_compute_extenso',
    )
    extenso_singular_decimal = fields.Char(
        string='Ex. 1,67',
        compute='_compute_extenso',
    )
    extenso_plural_decimal = fields.Char(
        string='Ex. 1.234.567,89',
        compute='_compute_extenso',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Símbolo para campos monetary',
        ondelete='restrict',
    )

    @api.depends('codigo')
    def _compute_codigo_unico(self):
        for unidade in self:
            codigo_unico = unidade.codigo or ''
            codigo_unico = codigo_unico.lower().strip()
            codigo_unico = codigo_unico.replace(' ', ' ')
            codigo_unico = codigo_unico.replace('²', '2')
            codigo_unico = codigo_unico.replace('³', '3')
            codigo_unico = tira_acentos(codigo_unico)
            unidade.codigo_unico = codigo_unico

    @api.depends('nome')
    def _compute_nome_unico(self):
        for unidade in self:
            nome_unico = unidade.nome or ''
            nome_unico = nome_unico.lower().strip()
            nome_unico = nome_unico.replace(' ', ' ')
            nome_unico = nome_unico.replace('²', '2')
            nome_unico = nome_unico.replace('³', '3')
            nome_unico = tira_acentos(nome_unico)
            unidade.nome_unico = nome_unico

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
                raise ValidationError('Código de unidade já existe!')

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
                raise ValidationError('Nome de unidade já existe!')

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

            args += [
                '|',
                ['codigo', '=', name],
                '|',
                ['codigo_unico', '=', name.lower()],
                '|',
                ['nome', operator, name],
                ['nome_unico', operator, name.lower()],
            ]
            unidades = self.search(args, limit=limit)
            return unidades.name_get()

        return super(SpedUnidade, self).name_search(name=name, args=args,
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
            category_id = self.env.ref(
                'product.product_uom_categ_area').id

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

    def prepare_sync_to_currency(self):
        self.ensure_one()

        dados = {
            'name': self.nome + ' - UNIDADE',
            'symbol': self.codigo,
            'is_uom': True,
            'active': True,
            'position': 'after',
        }

        if self.fator_relacao_decimal == 10:
            casas_decimais = self.precisao_decimal
        else:
            casas_decimais = \
                self.env.ref('l10n_br_base.CASAS_DECIMAIS_QUANTIDADE').digits

        casas_decimais = D(casas_decimais or 0)

        dados['rounding'] = D(10) ** (casas_decimais * -1)

        return dados

    @api.multi
    def sync_to_currency(self):
        for unidade in self:
            dados = unidade.prepare_sync_to_currency()

            if not unidade.currency_id:
                currency = self.env['res.currency'].sudo().create(dados)
                unidade.currency_id = currency.id
            else:
                unidade.currency_id.sudo().write(dados)

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
                'product.product_uom_categ_area').id

        elif dados['tipo'] == self.TIPO_UNIDADE_TEMPO:
            dados['category_id'] = self.env.ref('product.uom_categ_wtime').id

        unidade = super(SpedUnidade, self).create(dados)
        unidade.sync_to_uom()
        unidade.sync_to_currency()

        return unidade

    @api.multi
    def write(self, dados):
        if 'codigo' in dados:
            dados['name'] = dados['codigo']

        res = super(SpedUnidade, self).write(dados)
        self.sync_to_uom()
        self.sync_to_currency()
        return res
