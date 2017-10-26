# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning as UserError
from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from odoo.addons.l10n_br_base.constante_tributaria import FORMA_PAGAMENTO
from ..constantes import *

_logger = logging.getLogger(__name__)

try:
    from pybrasil.data import parse_datetime, hoje
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)


class FinanLancamento(SpedBase, models.Model):
    _name = b'finan.lancamento'
    _description = 'Lançamento Financeiro'
    _inherit = ['mail.thread']
    _order = 'data_vencimento_util, numero, id desc'
    _rec_name = 'nome'

    #
    # Identificação do lançamento
    #
    tipo = fields.Selection(
        string='Tipo',
        selection=FINAN_TIPO,
        required=True,
        index=True,
    )
    sinal = fields.Integer(
        string='Sinal',
        compute='_compute_sinal',
        store=True,
    )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        required=True,
        ondelete='restrict',
        default=lambda self: self.env['sped.empresa']._empresa_ativa('sped.empresa'),
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company original',
        related='empresa_id.company_id',
        store=True,
        readonly=True,
    )
    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        compute='_compute_cnpj_cpf',
        store=True,
        index=True,
    )
    cnpj_cpf_raiz = fields.Char(
        string='Raiz do CNPJ/CPF',
        compute='_compute_cnpj_cpf',
        store=True,
        index=True,
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Participante',
        ondelete='restrict',
        index=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner original',
        related='participante_id.partner_id',
        store=True,
        readonly=True,
    )
    documento_id = fields.Many2one(
        comodel_name='finan.documento',
        string='Tipo de documento',
        ondelete='restrict',
        index=True,
    )
    forma_pagamento_id = fields.Many2one(
        comodel_name='finan.forma.pagamento',
        string='Forma de pagamento',
        ondelete='restrict',
        index=True,
    )
    forma_pagamento = fields.Selection(
        selection=FORMA_PAGAMENTO,
        string='Forma de pagamento fiscal',
        related='forma_pagamento_id.forma_pagamento',
        readonly=True,
    )
    exige_numero = fields.Boolean(
        string='Exige número de documento?',
        related='forma_pagamento_id.exige_numero',
        readonly=True,
    )
    numero = fields.Char(
        string='Número do documento',
        index=True,
    )
    conta_id = fields.Many2one(
        comodel_name='finan.conta',
        string='Conta',
        index=True,
        required=True,
        domain=[('tipo', '=', 'A')],
    )

    #
    # Move dates; there are those five date fields, controlling, respectively:
    # data_documento - when de document to which the lancamento refers was created
    # data_vencimento - up to when the debt must be paid
    # data_vencimento_util - if data_vencimento is a weekend, when banks don't
    #    regularly open, or is on a weekday, that happens to be a holiday,
    #    lancamento.s the *real* data_vencimento to the next business day; when
    #    controlling customers' payments' regularity, if the customer pays
    #    his/her debt on the data_vencimento_util, it must still be
    #    considered a regular paying customer
    # data_pagamento - when the debt was actually paid
    # data_credito_debito - when *the bank* credits/debits the actual money
    #    in/out of the bank account (in certain cases, there is a 1 or 2 day
    #    delay between the customer pagamento and the actual liquidity of the
    #    pagamento on the bank account
    #
    data_documento = fields.Date(
        string='Data do documento',
        default=fields.Date.context_today,
        index=True,
    )
    data_vencimento = fields.Date(
        string='Data de vencimento',
        index=True,
    )
    data_vencimento_util = fields.Date(
        string='Data de vencimento útil',
        store=True,
        compute='_compute_data_vencimento_util',
        index=True,
    )
    dias_atraso = fields.Integer(
        string='Dias de atraso',
        compute='_compute_dias_atraso',
        store=True,
    )
    data_pagamento = fields.Date(
        string='Data de pagamento',
        copy=False,
        index=True,
        default=lambda lancamento: False if lancamento.tipo not in
            FINAN_TIPO_PAGAMENTO else fields.Date.context_today
    )
    data_credito_debito = fields.Date(
        string='Data de crédito/débito',
        copy=False,
        index=True,
    )
    data_baixa = fields.Date(
        string='Data de baixa',
        copy=False,
        index=True,
    )
    data_extrato = fields.Date(
        string='Data no extrato banco/caixa',
        compute='_compute_data_extrato',
        copy=False,
        store=True,
        index=True,
    )

    #
    # Valores do lançamento
    #
    vr_documento = fields.Monetary(
        string='Valor do documento',
    )
    vr_juros = fields.Monetary(
        string='Valor de juros',
    )
    vr_multa = fields.Monetary(
        string='Valor de multa',
    )
    vr_outros_creditos = fields.Monetary(
        string='Outros créditos',
    )
    vr_desconto = fields.Monetary(
        string='Valor de desconto',
    )
    vr_outros_debitos = fields.Monetary(
        string='Outros débitos',
    )
    vr_tarifas = fields.Monetary(
        string='Tarifas',
    )
    vr_adiantado = fields.Monetary(
        string='Valor adiantado',
    )
    vr_baixado = fields.Monetary(
        string='Valor baixado',
        compute='_compute_total_saldo',
        store=True,
    )
    vr_total = fields.Monetary(
        string='Total',
        compute='_compute_total',
        store=True,
    )

    #
    # Campos de valor que somam todos os pagamentos relacionados a uma dívida
    #
    vr_quitado_documento = fields.Monetary(
        string='Valor quitado do documento',
        compute='_compute_total_saldo',
        store=True,
    )
    vr_quitado_juros = fields.Monetary(
        string='Valor quitado de juros',
        compute='_compute_total_saldo',
        store=True,
    )
    vr_quitado_multa = fields.Monetary(
        string='Valor quitado de multa',
        compute='_compute_total_saldo',
        store=True,
    )
    vr_quitado_outros_creditos = fields.Monetary(
        string='Valor quitado de outros créditos',
        compute='_compute_total_saldo',
        store=True,
    )
    vr_quitado_desconto = fields.Monetary(
        string='Valor quitado de desconto',
        compute='_compute_total_saldo',
        store=True,
    )
    vr_quitado_outros_debitos = fields.Monetary(
        string='Valor quitado de outros débitos',
        compute='_compute_total_saldo',
        store=True,
    )
    vr_quitado_tarifas = fields.Monetary(
        string='Valor quitado de tarifas',
        compute='_compute_total_saldo',
        store=True,
    )
    vr_quitado_adiantado = fields.Monetary(
        string='Valor quitado adiantado',
        compute='_compute_total_saldo',
        store=True,
    )
    vr_quitado_baixado = fields.Monetary(
        string='Valor quitado baixado',
        compute='_compute_total_saldo',
        store=True,
    )
    vr_quitado_total = fields.Monetary(
        string='Valor quitado total',
        compute='_compute_total_saldo',
        store=True,
    )
    vr_saldo = fields.Monetary(
        string='Saldo',
        compute='_compute_total_saldo',
        store=True,
    )

    #
    # Previsão de juros e multa do lançamento
    #
    al_juros = fields.Monetary(
        string='Taxa de juros (mensal)',
        currency_field='currency_aliquota_id'
    )
    data_juros = fields.Date(
        string='Juros a partir de',
    )
    vr_juros_previsto = fields.Monetary(
        string='Valor de juros previsto',
    )
    al_multa = fields.Monetary(
        string='Percentual de multa',
        currency_field='currency_aliquota_id'
    )
    data_multa = fields.Date(
        string='Multa a partir de',
    )
    vr_multa_previsto = fields.Monetary(
        string='Valor de multa previsto',
    )
    al_desconto = fields.Monetary(
        string='Percentual de desconto',
        currency_field='currency_aliquota_id'
    )
    data_desconto = fields.Date(
        string='Desconto até',
    )
    vr_desconto_previsto = fields.Monetary(
        string='Valor de desconto previsto',
    )
    vr_total_previsto = fields.Monetary(
        string='Total previsto',
    )

    #
    # Relação com outras dívidas e pagamentos
    #
    divida_id = fields.Many2one(
        comodel_name='finan.lancamento',
        string='Dívida',
        domain=[('tipo', 'in', FINAN_TIPO_DIVIDA)],
        index=True,
    )
    pagamento_ids = fields.One2many(
        comodel_name='finan.lancamento',
        inverse_name='divida_id',
    )
    divida_ids = fields.One2many(
        comodel_name='finan.lancamento',
        compute='_compute_divida_ids',
    )

    #
    # Situação da dívida
    #
    situacao_divida = fields.Selection(
        string='Situação da dívida',
        selection=FINAN_SITUACAO_DIVIDA,
        compute='_compute_situacao_divida',
        store=True,
        index=True,
    )
    situacao_divida_simples = fields.Selection(
        string='Situação simples da dívida',
        selection=FINAN_SITUACAO_DIVIDA_SIMPLES,
        compute='_compute_situacao_divida',
        store=True,
        index=True,
    )
    provisorio = fields.Boolean(
        string='É provisório?',
        index=True,
    )
    state = fields.Selection(
        string='State',
        selection=FINAN_STATE,
        compute='_compute_situacao_divida',
        store=True,
        index=True,
    )

    #
    # Conta bancária/caixa onde o dinheiro entrou ou de onde saiu
    #
    banco_id = fields.Many2one(
        comodel_name='finan.banco',
        string='Conta bancária',
        ondelete='restrict',
        index=True,
    )
    banco = fields.Selection(
        selection=FINAN_BANCO,
        related='banco_id.banco',
        readonly=True,
    )
    extrato_id = fields.One2many(
        comodel_name='finan.banco.extrato',
        inverse_name='lancamento_id',
        string='Extrato banco/caixa',
    )
    vr_saldo_banco = fields.Monetary(
        string='Saldo banco/caixa após lançamento',
        related='extrato_id.saldo',
    )

    #
    # Carteira de cobrança/boletos
    #
    carteira_id = fields.Many2one(
        comodel_name='finan.carteira',
        string='Carteira',
        ondelete='restrict',
        index=True,
    )
    nosso_numero = fields.Char(
        string='Nosso número',
        size=20,
    )

    #
    # Histórico do lançamento
    #
    historico = fields.Text(
        string='Histórico',
    )

    #
    # Controle de parcelamentos
    #
    #parcelamento_simulacao_id = fields.Many2one(
        #comodel_name='finan.installment.simulation',
        #string='Installment simulation',
        #index=True,
        #ondelete='restrict',
    #)
    #parcelamento_id = fields.Many2one(
        #comodel_name='finan.installment',
        #string='Installment',
        #related='parcelamento_simulacao_id.parcelamento_id',
        #readonly=True,
        #store=True,
        #index=True,
        #ondelete='restrict',
    #)

    #
    # Controle de dívidas em outras moedas
    #
    currency_original_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moeda original da dívida',
        domain=[('is_currency', '=', True)]
    )
    vr_documento_original = fields.Monetary(
        string='Valor do documento na moeda original',
        currency_field='currency_original_id',
    )

    #
    #
    # Condições de pagamento
    #
    condicao_pagamento_id = fields.Many2one(
        comodel_name='account.payment.term',
        string="Condição de pagamento",
        ondelete='restrict',
        domain=[('forma_pagamento', '!=', False)],
    )

    #
    # Descrição do lançamento
    #
    nome = fields.Char(
        string='Lançamento',
        compute='_compute_nome',
        store=True,
        index=True,
    )

    #
    # Documento relacionado (campo genérico)
    #
    referencia_id = fields.Reference(
        selection=[],
        string='Documento relacionado',
        readonly=True,
    )

    #
    # Controle de baixa
    #
    permite_baixa = fields.Boolean(
        string='Permite baixa?',
        #compute='_compute_permite_baixa',
    )
    #motivo_baixa_id = fields.Many2one(
        #comodel_name='finan.motivo.baixa',
        #string="Motivo da baixa",
    #)

    @api.depends('tipo')
    def _compute_sinal(self):
        for lancamento in self:
            if lancamento.tipo in FINAN_TIPO_ENTRADA:
                lancamento.sinal = 1
            else:
                lancamento.sinal = -1

    @api.depends('empresa_id', 'empresa_id.cnpj_cpf')
    def _compute_cnpj_cpf(self):
        for lancamento in self:
            lancamento.cnpj_cpf = lancamento.empresa_id.cnpj_cpf
            lancamento.cnpj_cpf_raiz = lancamento.empresa_id.cnpj_cpf_raiz

    @api.depends('tipo', 'documento_id', 'numero', 'participante_id')
    def _compute_nome(self):
        for lancamento in self:
            nome = ''

            #if self._context.get('com_tipo'):
                #nome += FINAN_TIPO_CODIGO[lancamento.tipo]
                #nome += ' / '

            if lancamento.tipo in FINAN_TIPO_PAGAMENTO:
                if lancamento.forma_pagamento_id:
                    nome += lancamento.forma_pagamento_id.nome
                    nome += ' / '

            else:
                if lancamento.documento_id:
                    nome += lancamento.documento_id.nome
                    nome += ' / '

            nome += lancamento.numero or ''

            if self._context.get('com_participante'):
                nome += ' - '
                nome += lancamento_id.participante_id.name_get()[0][1]

            lancamento.nome = nome

    @api.depends('vr_documento',
                 'vr_juros', 'vr_multa', 'vr_outros_creditos',
                 'vr_desconto', 'vr_outros_debitos', 'vr_tarifas',
                 'vr_adiantado')
    def _compute_total(self):
        for lancamento in self:
            vr_total = D(lancamento.vr_documento)
            vr_total += D(lancamento.vr_juros)
            vr_total += D(lancamento.vr_multa)
            vr_total += D(lancamento.vr_outros_creditos)
            vr_total += D(lancamento.vr_adiantado)
            vr_total -= D(lancamento.vr_desconto)
            vr_total -= D(lancamento.vr_outros_debitos)
            vr_total -= D(lancamento.vr_tarifas)
            vr_total -= D(lancamento.vr_baixado)
            lancamento.vr_total = vr_total

    @api.depends('vr_documento',
                 'vr_juros', 'vr_multa', 'vr_outros_creditos',
                 'vr_desconto', 'vr_outros_debitos', 'vr_tarifas',
                 'vr_adiantado',
                 'pagamento_ids.vr_documento',
                 'pagamento_ids.vr_juros', 'pagamento_ids.vr_multa',
                 'pagamento_ids.vr_outros_creditos',
                 'pagamento_ids.vr_desconto',
                 'pagamento_ids.vr_outros_debitos',
                 'pagamento_ids.vr_tarifas',
                 'pagamento_ids.vr_adiantado',
                 'pagamento_ids.situacao_divida'
                 )
    def _compute_total_saldo(self):
        for lancamento in self:
            vr_quitado_documento = D(0)
            vr_quitado_juros = D(0)
            vr_quitado_multa = D(0)
            vr_quitado_outros_creditos = D(0)
            vr_quitado_desconto = D(0)
            vr_quitado_outros_debitos = D(0)
            vr_quitado_tarifas = D(0)
            vr_quitado_adiantado = D(0)
            vr_quitado_baixado = D(0)
            vr_quitado_total = D(0)

            vr_total = D(lancamento.vr_total)
            vr_saldo = D(0)

            if lancamento.tipo in FINAN_TIPO_DIVIDA:
                for pagamento in lancamento.pagamento_ids:
                    #
                    # Não considera pagamentos que tenham controle de data
                    # da crédito/débito exigido pela forma de pagamento
                    #
                    if pagamento.situacao_divida != \
                        FINAN_SITUACAO_DIVIDA_QUITADO:
                        continue

                    vr_quitado_documento += D(pagamento.vr_documento)
                    vr_quitado_juros += D(pagamento.vr_juros)
                    vr_quitado_multa += D(pagamento.vr_multa)
                    vr_quitado_outros_creditos += \
                        D(pagamento.vr_outros_creditos)
                    vr_quitado_desconto += D(pagamento.vr_desconto)
                    vr_quitado_outros_debitos += D(pagamento.vr_outros_debitos)
                    vr_quitado_tarifas += D(pagamento.vr_tarifas)
                    vr_quitado_adiantado += D(pagamento.vr_adiantado)
                    vr_quitado_baixado += D(pagamento.vr_baixado)
                    vr_quitado_total += D(pagamento.vr_total)

                vr_saldo = vr_total - vr_quitado_documento

                if vr_saldo < 0:
                    vr_saldo = D(0)

                lancamento.vr_saldo = vr_saldo

                if lancamento.data_baixa:
                    lancamento.vr_baixado = vr_saldo

                lancamento.vr_adiantado = vr_quitado_adiantado

            lancamento.vr_quitado_documento = vr_quitado_documento
            lancamento.vr_quitado_juros = vr_quitado_juros
            lancamento.vr_quitado_multa = vr_quitado_multa
            lancamento.vr_quitado_outros_creditos = vr_quitado_outros_creditos
            lancamento.vr_quitado_desconto = vr_quitado_desconto
            lancamento.vr_quitado_outros_debitos = vr_quitado_outros_debitos
            lancamento.vr_quitado_tarifas = vr_quitado_tarifas
            lancamento.vr_quitado_adiantado = vr_quitado_adiantado
            lancamento.vr_quitado_baixado = vr_quitado_baixado
            lancamento.vr_quitado_total = vr_quitado_total

    @api.depends('data_vencimento', 'documento_id.antecipa_vencimento',
                 'empresa_id.municipio_id')
    def _compute_data_vencimento_util(self):
        for lancamento in self:
            if not lancamento.data_vencimento:
                continue

            data_vencimento_util = lancamento.empresa_id.dia_util(
                lancamento.data_vencimento,
                lancamento.documento_id.antecipa_vencimento
            )
            lancamento.data_vencimento_util = data_vencimento_util

    @api.depends('data_documento', 'data_pagamento', 'data_credito_debito')
    def _compute_data_extrato(self):
        for lancamento in self:
            if lancamento.data_credito_debito:
                lancamento.data_extrato = lancamento.data_credito_debito
            elif lancamento.data_pagamento:
                lancamento.data_extrato = lancamento.data_pagamento
            elif lancamento.data_documento:
                lancamento.data_extrato = lancamento.data_documento

    @api.depends('data_vencimento_util', 'vr_total', 'vr_documento',
                 'vr_saldo', 'vr_quitado_documento', 'data_baixa',
                 'data_credito_debito', 'provisorio')
    def _compute_situacao_divida(self):
        for lancamento in self:
            if lancamento.tipo in FINAN_TIPO_DIVIDA:
                if lancamento.data_baixa:
                    if lancamento.vr_quitado_documento > 0:
                        lancamento.situacao_divida = \
                            FINAN_SITUACAO_DIVIDA_BAIXADO_PARCIALMENTE
                    else:
                        lancamento.situacao_divida = \
                            FINAN_SITUACAO_DIVIDA_BAIXADO

                elif lancamento.vr_quitado_documento > 0:
                    if lancamento.vr_saldo > 0:
                        lancamento.situacao_divida = \
                            FINAN_SITUACAO_DIVIDA_QUITADO_PARCIALMENTE
                    else:
                        lancamento.situacao_divida = \
                            FINAN_SITUACAO_DIVIDA_QUITADO

                elif lancamento.data_vencimento_util:
                    data_hoje = hoje()
                    data_vencimento = parse_datetime(
                        lancamento.data_vencimento_util).date()

                    if data_vencimento < data_hoje:
                        lancamento.situacao_divida = \
                            FINAN_SITUACAO_DIVIDA_VENCIDO

                    elif data_vencimento == data_hoje:
                        lancamento.situacao_divida = \
                            FINAN_SITUACAO_DIVIDA_VENCE_HOJE

                    else:
                        lancamento.situacao_divida = \
                            FINAN_SITUACAO_DIVIDA_A_VENCER

                else:
                    lancamento.situacao_divida = \
                        FINAN_SITUACAO_DIVIDA_A_VENCER

            #
            # Controla a situação das formas de pagamento que exigem a
            # informação da data de crédito/débito (caso dos cheques)
            #
            elif lancamento.tipo in FINAN_TIPO_PAGAMENTO:
                if lancamento.forma_pagamento_id.quitado_somente_com_data_credito_debito:
                    if lancamento.data_credito_debito:
                        lancamento.situacao_divida = \
                            FINAN_SITUACAO_DIVIDA_QUITADO
                    else:
                        lancamento.situacao_divida = \
                            FINAN_SITUACAO_DIVIDA_VENCIDO
                else:
                    lancamento.situacao_divida = FINAN_SITUACAO_DIVIDA_QUITADO

            if lancamento.situacao_divida in \
                FINAN_SITUACAO_DIVIDA_CONSIDERA_ABERTO:
                lancamento.situacao_divida_simples = \
                    FINAN_SITUACAO_DIVIDA_SIMPLES_ABERTO

            elif lancamento.situacao_divida in \
                FINAN_SITUACAO_DIVIDA_CONSIDERA_QUITADO:
                lancamento.situacao_divida_simples = \
                    FINAN_SITUACAO_DIVIDA_SIMPLES_QUITADO

            elif lancamento.situacao_divida in \
                FINAN_SITUACAO_DIVIDA_CONSIDERA_BAIXADO:
                lancamento.situacao_divida_simples = \
                    FINAN_SITUACAO_DIVIDA_SIMPLES_BAIXADO

            if lancamento.situacao_divida == \
                FINAN_SITUACAO_DIVIDA_QUITADO:
                lancamento.state = FINAN_STATE_PAID

            elif lancamento.situacao_divida_simples == \
                FINAN_SITUACAO_DIVIDA_SIMPLES_BAIXADO:
                lancamento.state = FINAN_STATE_CANCELLED

            elif lancamento.provisorio:
                lancamento.state = FINAN_STATE_DRAFT

            else:
                lancamento.state = FINAN_STATE_OPEN

    @api.depends('divida_id')
    def _compute_divida_ids(self):
        for pagamento in self:
            if pagamento.divida_id:
                pagamento.divida_ids = [pagamento.divida_id.id]
            else:
                pagamento.divida_ids = False

    @api.onchange('empresa_id')
    def _onchange_empresa_id(self):
        for lancamento in self:
            lancamento.cnpj_cpf = lancamento.empresa_id.cnpj_cpf
            lancamento.cnpj_cpf_raiz = lancamento.empresa_id.cnpj_cpf_raiz

    @api.onchange('forma_pagamento_id')
    def _onchange_forma_pagamento_id(self):
        for lancamento in self:
            if lancamento.forma_pagamento_id.documento_id:
                lancamento.documento_id = \
                    lancamento.forma_pagamento_id.documento_id

    @api.depends('empresa_id.data_referencia_financeira')
    def _compute_dias_atraso(self):
        for lancamento in self:
            if lancamento.tipo not in FINAN_TIPO_DIVIDA:
                continue

            data_vencimento_util = \
                parse_datetime(lancamento.data_vencimento_util).date()

            if lancamento.data_pagamento:
                data_base = parse_datetime(lancamento.data_pagamento).date()
            else:
                data_base = hoje()

            dias_atraso = (data_base - data_vencimento_util).days

            lancamento.dias_atraso = dias_atraso

    @api.constrains('vr_documento',
                    'vr_juros', 'vr_multa', 'vr_outros_creditos',
                    'vr_desconto', 'vr_outros_debitos', 'vr_tarifas',
                    'vr_total', 'vr_adiantado')
    def _check_amount(self):
        for lancamento in self:
            if lancamento.vr_documento < 0:
                raise ValidationError('O valor do documento precisa ser maior'
                    ' do que zero!')
            elif lancamento.vr_documento == 0:
                raise ValidationError('O valor do documento não pode ser'
                    ' zero!')

            if lancamento.vr_juros < 0:
                raise ValidationError('O valor dos juros precisa ser maior'
                    ' do que zero!')

            if lancamento.vr_multa < 0:
                raise ValidationError('O valor da multa precisa ser maior'
                    ' do que zero!')

            if lancamento.vr_outros_creditos < 0:
                raise ValidationError('O valor de outros créditos precisa ser '
                    'maior do que zero!')

            if lancamento.vr_desconto < 0:
                raise ValidationError('O valor do desconto precisa ser maior'
                    ' do que zero!')

            if lancamento.vr_outros_debitos < 0:
                raise ValidationError('O valor de outros débitos precisa ser '
                    'maior do que zero!')

            if lancamento.vr_tarifas < 0:
                raise ValidationError('O valor das tarifas precisa ser maior'
                    ' do que zero!')

            if lancamento.vr_total < 0:
                raise ValidationError('O valor total precisa ser maior'
                    ' do que zero!')

            #
            # Quando houver o consumo do adiantamento, esse não pode ser maior
            # do que o valor do documento em valores absolutos
            #
            if lancamento.vr_adiantado < 0:
                if (lancamento.vr_adiantado * -1) > lancamento.vr_documento:
                    raise ValidationError('O valor utilizado do saldo de '
                        'adiantamento não pode ser maior do que o valor '
                        'do documento!')


    #@api.model
    #def _avaliable_transition(self, old_state, new_state):
        #allowed = [
            #('draft', 'open'),
            #('open', 'paid'),
            #('open', 'cancelled'),
            #('paid', 'open'),
        #]
        #return (old_state, new_state) in allowed

    def _verifica_ajusta_extrato_saldo(self, bancos={}):
        for lancamento in self:
            if not (lancamento.tipo in FINAN_LANCAMENTO_ENTRADA or \
                lancamento.tipo in FINAN_LANCAMENTO_SAIDA):
                continue

            banco_id = lancamento.banco_id.id
            if banco_id not in bancos:
                bancos[banco_id] = lancamento.data_extrato
            elif bancos[banco_id] > lancamento.data_extrato:
                bancos[banco_id] = lancamento.data_extrato

    def _ajusta_extrato_saldo(self, bancos={}):
        for banco_id in bancos:
            data = bancos[banco_id]
            self.env['finan.banco.extrato'].ajusta_extrato(banco_id, data)
            self.env['finan.banco.saldo'].ajusta_saldo(banco_id, data)

    def executa_antes_create(self, dados, bancos={}):
        return dados

    @api.model
    def create(self, dados):
        dados = self.executa_antes_create(dados)
        res = super(FinanLancamento, self).create(dados)
        return self.executa_depois_create(res, dados)

    def executa_depois_create(self, result, dados):
        bancos = {}
        result._verifica_ajusta_extrato_saldo(bancos)
        self._ajusta_extrato_saldo(bancos)
        return result

    def executa_antes_write(self, dados, bancos={}):
        self._verifica_ajusta_extrato_saldo(bancos)
        return dados

    def write(self, dados):
        bancos = {}
        self.executa_antes_write(dados, bancos)
        result = super(FinanLancamento, self).write(dados)
        return self.executa_depois_write(result, dados, bancos)

    def executa_depois_write(self, result, dados, bancos={}):
        self._verifica_ajusta_extrato_saldo(bancos)
        self._ajusta_extrato_saldo(bancos)
        return result

    def executa_antes_unlink(self, bancos={}):
        for lancamento in self:
            if lancamento.referencia_id:
                raise UserError('Você não pode excuir um lançamento '
                    'relacionado a outro documento; verifique se é possível '
                    'cancelar o documento relacionado.')

            if lancamento.provisorio:
                continue

            #
            # Pagamentos podem ser excluídos desde que o caixa não tenha
            # fechado
            #
            if lancamento.tipo in FINAN_TIPO_PAGAMENTO:
                continue

            if lancamento.situacao_divida_simples == \
                FINAN_SITUACAO_DIVIDA_SIMPLES_ABERTO:
                continue

            if lancamento.situacao_divida_simples == \
                FINAN_SITUACAO_DIVIDA_SIMPLES_BAIXADO:
                raise UserError('Você não pode excuir um lançamento baixado!')

            if lancamento.situacao_divida_simples == \
                FINAN_SITUACAO_DIVIDA_SIMPLES_QUITADO:
                raise UserError('Você não pode excuir um lançamento com '
                                'pagamentos!')

            lancamento._verifica_ajusta_extrato_saldo(bancos)

    def unlink(self):
        bancos = {}
        self.executa_antes_unlink(bancos)
        res = super(FinanLancamento, self).unlink()
        return self.executa_depois_unlink(res, bancos)

    def executa_depois_unlink(self, result, bancos={}):
        self._ajusta_extrato_saldo(bancos)
        return result

    def confirma_lancamento(self):
        for lancamento in self:
            if lancamento.provisorio:
                lancamento.provisorio = False

    def reabre_lancamento(self):
        for lancamento in self:
            if not lancamento.provisorio:
                if lancamento.situacao_divida_simples == \
                    FINAN_SITUACAO_DIVIDA_SIMPLES_ABERTO:
                    lancamento.provisorio = True
                else:
                    if lancamento.situacao_divida_simples == \
                        FINAN_SITUACAO_DIVIDA_SIMPLES_BAIXADO:
                        mensagem = 'Você não pode reabrir um lançamento ' + \
                                   'já baixado!'
                    else:
                        mensagem = 'Você não pode reabrir um lançamento ' + \
                                   'com pagamentos!'

                    raise UserError(mensagem)

    @staticmethod
    def _prepare_financial_lancamento(
            data_vencimento,
            vr_documento,
            numero,
            participante_id, type, data_documento,
            bank_id, empresa_id, currency_id,
            analytic_conta_id=False, conta_id=False,
            payment_term_id=False,
            **kwargs):
        return dict(
            bank_id=bank_id,
            empresa_id=empresa_id,
            currency_id=currency_id,
            type=type,
            participante_id=participante_id,
            numero=numero,
            data_documento=data_documento,
            payment_term_id=payment_term_id,
            analytic_conta_id=analytic_conta_id,
            conta_id=conta_id,
            data_vencimento=data_vencimento,
            vr_documento=vr_documento,
            **kwargs
        )

    @api.multi
    def create_lancamento(self):
        if not self.id:
            super(FinanLancamento, self).create()
        context = dict(self.env.context)

        form = self.env.ref('finan.finan_lancamento_pagamento_one2many_recebimento2_form',
                            True)
        return {
            'view_type': 'form',
            'view_id': [form.id],
            'view_mode': 'form',
            'res_model': 'finan.lancamento.wizard',
            'views': [(form.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }


            #def action_view_financial(self, type):
        #if type == '2receive':
            #action = self.env.ref(
                #'finan.financial_lancamento._debt_2receive_form_action').read()[0]
        #elif type == '2pay':
            #action = self.env.ref(
                #'finan.financial_lancamento._debt_2pay_form_action').read()[0]
        #if len(self) > 1:
            #action['domain'] = [('id', 'in', self.ids)]
        #elif len(self) == 1:
            ## action['views'] = \
            ##     [(
            ##         self.env.ref('finan.financial_lancamento._form_view').id,
            ##         'form',
            ##     )]
            #action['res_id'] = self.ids[0]
        #else:
            #action = {'type': 'ir.actions.act_window_close'}
        #return action


    # def _create_from_dict(self, lancamento._dict):
    #     '''How to use:
    #
    # def _prepare_lancamento_item(self, item):
    #      return {
    #          'numero':
    #              '{0.serie}-{0.numero:0.0f}-{1.numero}/{2}'.format(
    #                  self, item, len(self.duplicata_ids)),
    #          'data_vencimento': item.data_vencimento,
    #          'amount': item.valor
    #      }
    #
    #  def _prepare_lancamento_financeiro(self):
    #      return {
    #          'date': self.data_emissao,
    #          'type': '2receive',
    #          'partner_id':
    #              self.participante_id and self.participante_id.partner_id.id,
    #          'referencia_id': self._name + ',' + str(self.id),
    #          'bank_id': 1,
    #          'empresa_id': self.empresa_id and self.empresa_id.empresa_id.id,
    #          'currency_id': self.currency_id.id,
    #          'payment_term_id':
    #              self.payment_term_id and self.payment_term_id.id or False,
    #          # 'account_type_id':
    #          # 'analytic_conta_id':
    #          # 'condicao_pagamento_id:
    #          'lines': [self._prepara_lancamento_item(parcela)
    #                    for parcela in self.duplicata_ids],
    #      }
    #
    #  def action_financial_create(self):
    #
    #      p = self._prepare_lancamento_financeiro()
    #      financial_lancamento._ids = self.env['finan.lancamento']._create_from_dict(p)
    #      financial_lancamento._ids.action_confirm()
    #
    #      :param lancamento._dict:
    #      :return: a lancamento set of finan.lancamento
    #      '''
    #      lines = lancamento._dict.pop('lines')
    #
    #      financial_lancamento._ids = self.env['finan.lancamento']
    #
    #      for item in lines:
    #          data_vencimento = item.pop('data_vencimento')
    #          vr_documento = item.pop('vr_documento')
    #          numero = item.pop('numero')
    #          #
    #          # Override lancamento._dict with item data!
    #          #
    #          kwargs = lancamento._dict.copy()
    #          kwargs.update(item)
    #
    #          values = self._prepare_financial_lancamento(
    #              data_vencimento=data_vencimento,
    #              vr_documento=vr_documento,
    #              numero=numero,
    #              **kwargs
    #          )
    #          financial = self.create(values)
    #          financial_lancamento._ids |= financial
    #      return financial_lancamento._ids

    #def _readonly_state(self):
        #return {'draft': [('readonly', False)]}

    #def _required_fields(self):
        #return True

    #def _track_visibility_onchange(self):
        #return 'onchange'

    #def cron_interest(self):
        #if self.env['resource.calendar'].data_eh_dia_util_bancario(
                #datetime.data_hoje()):
            #lancamento = self.search([
                #('state', '=', 'open'),
                #('data_vencimento_util', '<', datetime.data_hoje())])
            ## lancamento._compute_interest()
            #lancamento._compute_situacao_divida()

    #@api.depends('condicao_pagamento_id', 'vr_documento',
                 #'data_vencimento_util')
    #def _compute_interest(self):
        #for lancamento in self:
            #if self.env['resource.calendar']. \
                    #data_eh_dia_util_bancario(datetime.data_hoje()) and lancamento. \
                    #state == 'open' and \
                    #(datetime.data_hoje() > datetime.strptime
                        #(lancamento.data_vencimento_util, '%Y-%m-%d')):
                #day = (
                    #datetime.data_hoje() - datetime.strptime(
                        #lancamento.data_vencimento,
                        #'%Y-%m-%d'))
                #interest = lancamento.vr_documento * \
                    #(lancamento.condicao_pagamento_id.interest_percent * day.days) / 100

                #delay_fee = (lancamento.condicao_pagamento_id.
                             #delay_fee_percent / 100) * lancamento.vr_documento
                #lancamento.vr_juros = interest + delay_fee

    #def change_state(self, new_state):
        #for lancamento in self:
            #if lancamento._avaliable_transition(lancamento.state, new_state):
                #lancamento.state = new_state
            #elif lancamento.state == new_state:
                #return True
            #else:
                #raise UserError(_('This state transition is not allowed'))

    #def action_confirm(self):
        #for lancamento in self:
            #lancamento.change_state('open')

    #def action_budget(self):
        #for lancamento in self:
            #lancamento.change_state('budget')

    #def action_paid(self):
        #for lancamento in self:
            #lancamento.change_state('paid')
            #if lancamento.state == 'paid':
                #data_pagamento = \
                    #max([x.data_pagamento for x in lancamento.pagamento_ids])
                #lancamento.data_pagamento = data_pagamento

    #def action_estorno(self):
        #for lancamento in self:
            #lancamento.change_state('open')

    #def action_cancel(self, motivo_id, obs):
        #for lancamento in self:
            #lancamento.change_state('cancelled')
            #if lancamento.note:
                #new_note = lancamento.note + '\n' + obs
            #else:
                #new_note = obs
            #lancamento.write({
                #'motivo_baixa_id': motivo_id,
                #'vr_baixado': lancamento.vr_documento,
                #'note': new_note,
                #'vr_saldo': 0,
            #})
            #lancamento.with_context(no_email=True).message_post(body=new_note)


#class FinanLancamentoMotivoCancelamento(models.Model):
    #_name = b'finan.lancamento.motivo.cancelamento'
    #_rec_name = 'motivo_cancelamento'

    #motivo_cancelamento = fields.Char(
        #string="Motivo do Cancelamento",
        #required=True,
    #)
