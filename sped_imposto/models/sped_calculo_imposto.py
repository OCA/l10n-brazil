# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import *
from openerp.addons.l10n_br_base.models.sped_base import SpedBase

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedCalculoImposto(SpedBase):
    """ Definie informações essenciais para as operações brasileiras

    Para entender como usar este modelo verifique os módulos:
        - sped_sale
        - sped_purchase

        Mas por via das dúvidas siga os passos:

        - Escolha o modelo de negócios que você deseja tornar faturável para o
        Brasil;
        - Crie um módulo com o padrão l10n_MODELO ou sped_MODELO
        - Herde a classe que será no futuro o cabeçalho do documento fiscal
         da seguinte forma:

         from odoo.addons.sped_imposto.models.sped_calculo_imposto import (
            SpedCalculoImposto
         )

     class ModeloCabecalho(SpedCaluloImposto, models.Models):

        brazil_line_ids = fields.One2many(
            comodel_name='sale.order.line.brazil',
            inverse_name='order_id',
            string='Linhas',
            copy=True
        )

        def _get_date(self):
        # Return the document date Used in _amount_all_wrapper
            return self.date_order

        # Se o documento já criar a invoice injete os paramretros na criação.
        @api.multi
        def _prepare_invoice(self):
            vals = super(SaleOrder, self)._prepare_invoice()

            vals['empresa_id'] = self.empresa_id.id or False
            vals['participante_id'] = \
                self.participante_id.id or False
            vals['sped_operacao_produto_id'] = \
                self.sped_operacao_produto_id.id or False
            vals['sped_operacao_servico_id'] = \
                self.sped_operacao_servico_id.id or False
            vals['condicao_pagamento_id'] = \
                self.condicao_pagamento_id.id or False

            return vals

        @api.one
        @api.depends('order_line.price_total')
        def _amount_all(self):
            if not self.is_brazilian:
                return super(SaleOrder, self)._amount_all()
            return self._amount_all_brazil()
    """
    _abstract = False

    @api.model
    def _default_company_id(self):
        return self.env['res.company']._company_default_get(self._name)

    is_brazilian = fields.Boolean(
        string='Is a Brazilian?',
        compute='_compute_is_brazilian',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
    )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        default=lambda self: self.env['sped.empresa']._empresa_ativa('sped.empresa')
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Destinatário/Remetente'
    )
    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação Fiscal',
    )
    condicao_pagamento_id = fields.Many2one(
        comodel_name='account.payment.term',
        string='Condição de pagamento',
        domain=[('forma_pagamento', '!=', False)],
    )
    regime_tributario = fields.Selection(
        selection=REGIME_TRIBUTARIO,
        string='Regime tributário',
        related='operacao_id.regime_tributario',
    )

    #
    # Totais dos itens
    #
    vr_produtos = fields.Monetary(
        string='Valor dos produtos/serviços',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_produtos_tributacao = fields.Monetary(
        string='Valor dos produtos para tributação',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_frete = fields.Monetary(
        string='Valor do frete',
        compute='_compute_soma_itens',
        store=True,
        inverse='_inverse_rateio_vr_frete',
    )
    vr_seguro = fields.Monetary(
        string='Valor do seguro',
        compute='_compute_soma_itens',
        store=True,
        inverse='_inverse_rateio_vr_seguro',
    )
    # al_desconto = fields.Monetary(
    #     string='Alíquota do desconto',
    #     currency_field='currency_aliquota_rateio_id',
    #     digits=(18, 11),
    #     compute='_compute_soma_itens',
    #     store=True,
    #     inverse='_inverse_rateio_al_desconto',
    # )
    vr_desconto = fields.Monetary(
        string='Valor do desconto',
        compute='_compute_soma_itens',
        store=True,
        inverse='_inverse_rateio_vr_desconto',
    )
    vr_outras = fields.Monetary(
        string='Outras despesas acessórias',
        compute='_compute_soma_itens',
        store=True,
        inverse='_inverse_rateio_vr_outras',
    )
    vr_operacao = fields.Monetary(
        string='Valor da operação',
        compute='_compute_soma_itens',
        store=True
    )
    vr_operacao_tributacao = fields.Monetary(
        string='Valor da operação para tributação',
        compute='_compute_soma_itens',
        store=True
    )
    # ICMS próprio
    bc_icms_proprio = fields.Monetary(
        string='Base do ICMS próprio',
        compute='_compute_soma_itens',
        store=True
    )
    vr_icms_proprio = fields.Monetary(
        string='Valor do ICMS próprio',
        compute='_compute_soma_itens',
        store=True
    )
    vr_icms_desonerado = fields.Monetary(
        string='Valor do ICMS desonerado',
        compute='_compute_soma_itens',
        store=True
    )
    # ICMS SIMPLES
    vr_icms_sn = fields.Monetary(
        string='Valor do crédito de ICMS - SIMPLES Nacional',
        compute='_compute_soma_itens',
        store=True
    )
    vr_simples = fields.Monetary(
        string='Valor do SIMPLES Nacional',
        compute='_compute_soma_itens',
        store=True,
    )
    # ICMS ST
    bc_icms_st = fields.Monetary(
        string='Base do ICMS ST',
        compute='_compute_soma_itens',
        store=True
    )
    vr_icms_st = fields.Monetary(
        string='Valor do ICMS ST',
        compute='_compute_soma_itens',
        store=True,
    )
    # ICMS ST retido
    bc_icms_st_retido = fields.Monetary(
        string='Base do ICMS retido anteriormente por '
               'substituição tributária',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_icms_st_retido = fields.Monetary(
        string='Valor do ICMS retido anteriormente por '
               'substituição tributária',
        compute='_compute_soma_itens',
        store=True,
    )
    # IPI
    bc_ipi = fields.Monetary(
        string='Base do IPI',
        compute='_compute_soma_itens',
        store=True
    )
    vr_ipi = fields.Monetary(
        string='Valor do IPI',
        compute='_compute_soma_itens',
        store=True,
    )
    # Imposto de importação
    bc_ii = fields.Monetary(
        string='Base do imposto de importação',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_despesas_aduaneiras = fields.Monetary(
        string='Despesas aduaneiras',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_ii = fields.Monetary(
        string='Valor do imposto de importação',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_iof = fields.Monetary(
        string='Valor do IOF',
        compute='_compute_soma_itens',
        store=True,
    )
    # PIS e COFINS
    bc_pis_proprio = fields.Monetary(
        string='Base do PIS próprio',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_pis_proprio = fields.Monetary(
        string='Valor do PIS próprio',
        compute='_compute_soma_itens',
        store=True,
    )
    bc_cofins_proprio = fields.Monetary(
        string='Base da COFINS própria',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_cofins_proprio = fields.Monetary(
        string='Valor do COFINS própria',
        compute='_compute_soma_itens',
        store=True,
    )
    # bc_pis_st = fields.Monetary(
    # 'Base do PIS ST', compute='_compute_soma_itens', store=True)
    # vr_pis_st = fields.Monetary(
    # 'Valor do PIS ST', compute='_compute_soma_itens', store=True)
    # bc_cofins_st = fields.Monetary(
    # 'Base da COFINS ST', compute='_compute_soma_itens', store=True)
    # vr_cofins_st = fields.Monetary(
    # 'Valor do COFINS ST', compute='_compute_soma_itens', store=True)
    #
    # Totais dos itens (grupo ISS)
    #
    # ISS
    bc_iss = fields.Monetary(
        string='Base do ISS',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_iss = fields.Monetary(
        string='Valor do ISS',
        compute='_compute_soma_itens',
        store=True,
    )
    # Total da NF e da fatura (podem ser diferentes no caso de operação
    # triangular)
    vr_nf = fields.Monetary(
        string='Valor da NF',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_fatura = fields.Monetary(
        string='Valor da fatura',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_ibpt = fields.Monetary(
        string='Valor IBPT',
        compute='_compute_soma_itens',
        store=True,
    )
    bc_inss_retido = fields.Monetary(
        string='Base do INSS',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_inss_retido = fields.Monetary(
        string='Valor do INSS',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_custo_comercial = fields.Monetary(
        string='Custo comercial',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_difal = fields.Monetary(
        string='Valor do diferencial de alíquota ICMS próprio',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_icms_estado_origem = fields.Monetary(
        string='Valor do ICMS para o estado origem',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_icms_estado_destino = fields.Monetary(
        string='Valor do ICMS para o estado destino',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_fcp = fields.Monetary(
        string='Valor do fundo de combate à pobreza',
        compute='_compute_soma_itens',
        store=True,
    )
    #
    # Total do peso
    #
    peso_bruto = fields.Monetary(
        string='Peso bruto',
        currency_field='currency_peso_id',
        compute='_compute_soma_itens',
        store=True,
    )
    peso_liquido = fields.Monetary(
        string='Peso líquido',
        currency_field='currency_peso_id',
        compute='_compute_soma_itens',
        store=True,
    )
    #
    # Transporte
    #
    modalidade_frete = fields.Selection(
        selection=MODALIDADE_FRETE,
        string='Modalidade do frete',
    )
    transportadora_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Transportadora',
        ondelete='restrict',
    )
    veiculo_id = fields.Many2one(
        comodel_name='sped.veiculo',
        string='Veículo',
        ondelete='restrict',
    )
    presenca_comprador = fields.Selection(
        selection=INDICADOR_PRESENCA_COMPRADOR,
        string='Presença do comprador',
    )

    # item_ids = fields.One2many(
    #     comodel_name='sped.calculo.imposto.item',
    #     inverse_name='documento_id',
    #     string='Itens',
    #     copy=True,
    # )


    @api.depends('company_id', 'partner_id')
    def _compute_is_brazilian(self):
        for documento in self:
            if documento.company_id.country_id:
                if documento.company_id.country_id.id == \
                        self.env.ref('base.br').id:
                    documento.is_brazilian = True

                    if documento.partner_id.sped_participante_id:
                        documento.participante_id = \
                            documento.partner_id.sped_participante_id

                    if documento.empresa_id:
                        if 'operacao_produto_id' in documento._fields:
                            if (documento.participante_id.tipo_pessoa ==
                                    TIPO_PESSOA_FISICA):
                                documento.operacao_produto_id = \
                                    documento.empresa_id.\
                                    operacao_produto_pessoa_fisica_id
                            else:
                                documento.operacao_produto_id = \
                                    documento.empresa_id.operacao_produto_id

                        if 'operacao_servico_id' in documento._fields:
                            documento.operacao_servico_id = \
                                documento.empresa_id.operacao_servico_id
                    continue
            documento.is_brazilian = False

    def _sincroniza_empresa_company_participante_partner(self):
        for documento in self:
            documento.company_id = documento.empresa_id.company_id
            documento.partner_id = documento.participante_id.partner_id

    @api.onchange('empresa_id', 'participante_id')
    def _onchange_empresa_participante(self):
        self._sincroniza_empresa_company_participante_partner()

    @api.depends('empresa_id', 'participante_id')
    def _depends_empresa_participante(self):
        self._sincroniza_empresa_company_participante_partner()

    @api.onchange('item_ids')
    def _onchange_soma_itens(self):
        self._compute_soma_itens()

    @api.depends('item_ids.vr_produtos', 'item_ids.vr_produtos_tributacao',
                'item_ids.vr_frete', 'item_ids.vr_seguro',
                'item_ids.vr_desconto', 'item_ids.vr_outras',
                'item_ids.vr_operacao', 'item_ids.vr_operacao_tributacao',
                'item_ids.bc_icms_proprio', 'item_ids.vr_icms_proprio',
                'item_ids.vr_icms_desonerado',
                'item_ids.vr_difal', 'item_ids.vr_icms_estado_origem',
                'item_ids.vr_icms_estado_destino',
                'item_ids.vr_fcp',
                'item_ids.vr_icms_sn', 'item_ids.vr_simples',
                'item_ids.bc_icms_st', 'item_ids.vr_icms_st',
                'item_ids.bc_icms_st_retido', 'item_ids.vr_icms_st_retido',
                'item_ids.bc_ipi', 'item_ids.vr_ipi',
                'item_ids.bc_ii', 'item_ids.vr_ii',
                'item_ids.vr_despesas_aduaneiras', 'item_ids.vr_iof',
                'item_ids.bc_pis_proprio', 'item_ids.vr_pis_proprio',
                'item_ids.bc_cofins_proprio', 'item_ids.vr_cofins_proprio',
                'item_ids.bc_iss', 'item_ids.vr_iss',
                'item_ids.vr_nf', 'item_ids.vr_fatura',
                'item_ids.vr_ibpt',
                'item_ids.vr_custo_comercial',
                'item_ids.peso_bruto', 'item_ids.peso_liquido')
    def _compute_soma_itens(self):
        CAMPOS_SOMA_ITENS = [
            'vr_produtos', 'vr_produtos_tributacao',
            'vr_frete', 'vr_seguro', 'vr_desconto', 'vr_outras',
            'vr_operacao', 'vr_operacao_tributacao',
            'bc_icms_proprio', 'vr_icms_proprio',
            'vr_icms_desonerado',
            'vr_difal', 'vr_icms_estado_origem', 'vr_icms_estado_destino',
            'vr_fcp',
            'vr_icms_sn', 'vr_simples',
            'bc_icms_st', 'vr_icms_st',
            'bc_icms_st_retido', 'vr_icms_st_retido',
            'bc_ipi', 'vr_ipi',
            'bc_ii', 'vr_ii', 'vr_despesas_aduaneiras', 'vr_iof',
            'bc_pis_proprio', 'vr_pis_proprio',
            'bc_cofins_proprio', 'vr_cofins_proprio',
            'bc_iss', 'vr_iss',
            'vr_nf', 'vr_fatura',
            'vr_ibpt',
            'vr_custo_comercial',
            'peso_bruto', 'peso_liquido'
        ]

        for documento in self:
            dados = {}
            for campo in CAMPOS_SOMA_ITENS:
                dados[campo] = D(0)
                #
                # Soma dos campos totalizadores por tipo: produto, serviço
                # e mensalidade
                #
                if 'produtos_' + campo in documento._fields:
                    dados['produtos_' + campo] = D(0)
                if 'servicos_' + campo in documento._fields:
                    dados['servicos_' + campo] = D(0)
                if 'mensalidades_' + campo in documento._fields:
                    dados['mensalidades_' + campo] = D(0)

            for item in documento.item_ids:
                for campo in CAMPOS_SOMA_ITENS:
                    dados[campo] += D(getattr(item, campo, 0))

                    if 'produtos_' + campo in dados:
                        if getattr(item, 'tipo_item', False) == 'P':
                            dados['produtos_' + campo] += \
                                D(getattr(item, campo, 0))

                    if 'servicos_' + campo in dados:
                        if getattr(item, 'tipo_item', False) == 'S':
                            dados['servicos_' + campo] += \
                                D(getattr(item, campo, 0))

                    if 'mensalidades_' + campo in dados:
                        if getattr(item, 'tipo_item', False) == 'M':
                            dados['mensalidades_' + campo] += \
                                D(getattr(item, campo, 0))

            documento.update(dados)

    def _inverse_rateio_campo_total(self, campo, tipo_item=None):
        self.ensure_one()

        campo_rateio = campo
        campo_total = 'vr_produtos'

        if tipo_item == 'P':
            campo_rateio = 'produtos_' + campo
            campo_total = 'produtos_' + campo_total
        elif tipo_item == 'S':
            campo_rateio = 'servicos_' + campo
            campo_total = 'servicos_' + campo_total
        elif tipo_item == 'M':
            campo_rateio = 'mensalidades_' + campo
            campo_total = 'mensalidades_' + campo_total

        #
        # Guardamos o valor total aqui, pois a medida que os itens forem sendo
        # alterados, esse valor vai mudar, e vai zicar a proporção mais
        # abaixo
        #
        vr_total = D(getattr(self, campo_total, 0))
        vr_rateio = D(getattr(self, campo_rateio, 0))

        for item in self.item_ids:
            if tipo_item is not None:
                if item.tipo_item != tipo_item:
                    continue

            if vr_total == 0:
                proporcao = D(0)
            else:
                proporcao = D(item.vr_produtos)
                proporcao /= vr_total

            valor = vr_rateio * proporcao
            valor = valor.quantize(D('0.01'))
            item.write({campo: valor})
            item.calcula_impostos()

    #def _inverse_rateio_campo_al_desconto(self, tipo_item=None):
        #self.ensure_one()

        #campo_rateio = 'al_desconto'
        #campo_desconto = 'vr_desconto'
        #campo_total = 'vr_produtos'

        #if tipo_item == 'P':
            #campo_rateio = 'produtos_' + campo_rateio
            #campo_total = 'produtos_' + campo_total
            #campo_desconto = 'produtos_' + campo_desconto
        #elif tipo_item == 'S':
            #campo_rateio = 'servicos_' + campo_rateio
            #campo_total = 'servicos_' + campo_total
            #campo_desconto = 'servicos_' + campo_desconto
        #elif tipo_item == 'M':
            #campo_rateio = 'mensalidades_' + campo_rateio
            #campo_total = 'mensalidades_' + campo_total
            #campo_desconto = 'mensalidades_' + campo_desconto

        #vr_total = D(getattr(self, campo_total, 0))
        #al_desconto = D(getattr(self, campo_rateio, 0))
        #vr_desconto = vr_total * al_desconto / 100
        #vr_desconto = vr_desconto.quantize(D('0.01'))

        #self.write({campo_desconto: vr_desconto})

    def _inverse_rateio_vr_frete(self):
        self.ensure_one()
        self._inverse_rateio_campo_total('vr_frete')

    def _inverse_rateio_vr_seguro(self):
        self.ensure_one()
        self._inverse_rateio_campo_total('vr_seguro')

    def _inverse_rateio_vr_outras(self):
        self.ensure_one()
        self._inverse_rateio_campo_total('vr_outras')

    #def _inverse_rateio_al_desconto(self):
        #self.ensure_one()
        #self._inverse_rateio_campo_al_desconto()

    def _inverse_rateio_vr_desconto(self):
        self.ensure_one()
        self._inverse_rateio_campo_total('vr_desconto')

    @api.onchange('condicao_pagamento_id')
    def _onchange_condicao_pagamento_id(self):
        self.ensure_one()
        if 'payment_term_id' in self._fields:
            self.payment_term_id = self.condicao_pagamento_id

    @api.onchange('participante_id')
    def _onchange_participante_id(self):
        self.ensure_one()
        self.partner_id = self.participante_id.partner_id

        if self.participante_id.condicao_pagamento_id:
            self.condicao_pagamento_id = \
                self.participante_id.condicao_pagamento_id
        if self.participante_id.operacao_produto_id:
            self.operacao_id = self.participante_id.operacao_produto_id
        if self.participante_id.transportadora_id:
            self.transportadora_id = self.participante_id.transportadora_id

    def prepara_dados_documento(self):
        self.ensure_one()
        return {}

    def _gera_documento(self, operacao, itens):
        self.ensure_one()

        if not (operacao and len(itens) > 0):
            return

        dados = {
            'empresa_id': self.empresa_id.id,
            'operacao_id': operacao.id,
            'modelo': operacao.modelo,
            'emissao': operacao.emissao,
            'participante_id': self.participante_id.id,
            'partner_id': self.partner_id.id,
            'condicao_pagamento_id': self.condicao_pagamento_id.id if \
                self.condicao_pagamento_id else False,
            'transportadora_id': self.transportadora_id.id if \
                self.transportadora_id else False,
            'modalidade_frete': self.modalidade_frete,
        }
        dados.update(self.prepara_dados_documento())

        #
        # Criamos o documento e chamados os onchange necessários
        #
        if isinstance(self.id, models.NewId):
            documento = self.env['sped.documento'].create(dados)
        else:
            documento = self

        if self.pagamento_ids:
            documento.pagamento_ids = self.pagamento_ids
        if self.duplicata_ids:
            documento.duplicata_ids = self.duplicata_ids

        documento.update(documento._onchange_empresa_id()['value'])
        documento.update(documento._onchange_operacao_id()['value'])

        if self.presenca_comprador:
            documento.presenca_comprador = self.presenca_comprador

        documento.update(documento._onchange_serie()['value'])
        documento.update(documento._onchange_participante_id()['value'])

        #
        # Criamos agora os itens do documento fiscal, e forçamos o recálculo
        # dos impostos, por segurança, caso alguma operação fiscal, alíquota
        # etc. tenha sido alterada
        #
        sped_documento_item = self.env['sped.documento.item']
        for item in itens:
            if isinstance(item.id, models.NewId):
                #
                #   Caso o registro seja um novo ID, geralmente vindo
                # de outro documento do sistema, com herança python.
                #   Para permir o preenchimento de dados de integração.
                #
                dados = {
                    'documento_id': documento.id,
                    'produto_id': item.produto_id.id,
                    'quantidade': item.quantidade,
                    'vr_unitario': item.vr_unitario,
                    'vr_frete': item.vr_frete,
                    'vr_seguro': item.vr_seguro,
                    'vr_desconto': item.vr_desconto,
                    'vr_outras': item.vr_outras,
                }
                dados.update(item.prepara_dados_documento_item())

                #
                #   Passamos o vr_unitario no contexto para evitar que as
                # configurações da operação redefinam o valor unitário durante
                # o cáculo dos impostos.
                #

                contexto = {
                    'forca_vr_unitario': dados['vr_unitario']
                }
                documento_item = sped_documento_item.create(dados)
            else:
                documento_item = item

            documento_item.with_context(contexto).calcula_impostos()

        #
        # Se certifica de que todos os campos foram totalizados
        #
        documento._compute_soma_itens()

        #
        # Agora que temos os itens, e por consequência o total do documento,
        # aplicamos a condição de pagamento
        #
        if self.condicao_pagamento_id:
            documento.condicao_pagamento_id = self.condicao_pagamento_id

        if documento.pagamento_ids:
            for pagamento in documento.pagamento_ids:
                pagamento.update(
                    pagamento._onchange_condicao_pagamento_id()['value']
                )
        else:
            documento.update(
                documento._onchange_condicao_pagamento_id()['value']
            )

        return documento

    def gera_documento(self):
        self.ensure_one()

        if not self.operacao_id:
            return

        return self._gera_documento(self.operacao_id, self.item_ids)

    def _mantem_sincronia_cadastros(self, dados):
        dados = \
            super(SpedCalculoImposto, self)._mantem_sincronia_cadastros(dados)

        #
        # Outros campos não many2one
        #
        CAMPOS = [
            ['price_unit', 'vr_unitario'],
            ['quantity', 'quantidade'],
            ['product_qty', 'quantidade'],
            ['product_uom_qty', 'quantidade'],
        ]
        for campo_original, campo_brasil in CAMPOS:
            if campo_original in dados and not campo_brasil in dados:
                dados[campo_brasil] = dados[campo_original]

        return dados

    @api.multi
    def action_view_documento(self):
        action = self.env.ref('sped.sped_documento_emissao_nfe_acao').read()[0]

        if len(self.documento_ids) > 1:
            action['domain'] = [('id', 'in', self.documento_ids.ids)]

        elif len(self.documento_ids) == 1:
            action['views'] = [
                (self.env.ref('sped.sped_documento_emissao_nfe_form').id,
                 'form')]
            action['res_id'] = self.documento_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}

        return action

    def _grava_anexo(self, nome_arquivo='', conteudo='',
                     tipo='application/xml', model='sped.documento'):
        self.ensure_one()

        attachment = self.env['ir.attachment']

        busca = [
            ('res_model', '=', model),
            ('res_id', '=', self.id),
            ('name', '=', nome_arquivo),
        ]
        attachment_ids = attachment.search(busca)
        attachment_ids.unlink()

        dados = {
            'name': nome_arquivo,
            'datas_fname': nome_arquivo,
            'res_model': model,
            'res_id': self.id,
            'datas': conteudo.encode('base64'),
            'mimetype': tipo,
        }

        anexo_id = self.env['ir.attachment'].create(dados)

        return anexo_id
