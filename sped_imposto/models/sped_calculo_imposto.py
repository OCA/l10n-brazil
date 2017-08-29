# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models, _
from openerp.addons.l10n_br_base.tools.misc import calc_price_ratio
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL_EMISSAO_PRODUTO,
    MODELO_FISCAL_EMISSAO_SERVICO,
    TIPO_PESSOA_FISICA,
)
from openerp.addons.l10n_br_base.models.sped_base import (
    SpedBase
)

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
        default=_default_company_id,
    )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        related='company_id.sped_empresa_id',
        string='Empresa',
        readonly=True,
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

    # item_ids = fields.One2many(
    #     comodel_name='sped.calculo.imposto.item',
    #     inverse_name='documento_id',
    #     string='Itens',
    #     copy=True,
    # )

    ind_pres = fields.Selection(
        selection=[
            ('0', 'Não se aplica'),
            ('1', 'Operação presencial'),
            ('2', 'Operação não presencial, pela Internet'),
            ('3', 'Operação não presencial, Teleatendimento'),
            ('4', 'NFC-e em operação com entrega em domicílio'),
            ('9', 'Operação não presencial, outros')
        ],
        string='Tipo de operação',
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=False,
        help='Indicador de presença do comprador no estabelecimento '
             'comercial no momento da operação.',
        default=lambda
            self: self.env.user.company_id.sped_empresa_id.ind_pres,
    )

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
                        if 'sped_operacao_produto_id' in documento._fields:
                            if (documento.participante_id.tipo_pessoa ==
                                    TIPO_PESSOA_FISICA):
                                documento.sped_operacao_produto_id = \
                                    documento.empresa_id.\
                                    operacao_produto_pessoa_fisica_id
                            else:
                                documento.sped_operacao_produto_id = \
                                    documento.empresa_id.operacao_produto_id

                        if 'sped_operacao_servico_id' in documento._fields:
                            documento.sped_operacao_servico_id = \
                                documento.empresa_id.operacao_servico_id
                    continue
            documento.is_brazilian = False

    @api.onchange('item_ids.vr_nf', 'item_ids.vr_fatura')
    def _onchange_soma_itens(self):
        self._compute_soma_itens()

    @api.depends('item_ids.vr_nf', 'item_ids.vr_fatura')
    def _compute_soma_itens(self):
        CAMPOS_SOMA_ITENS = [
            'vr_produtos', 'vr_produtos_tributacao',
            'vr_frete', 'vr_seguro', 'vr_desconto', 'vr_outras',
            'vr_operacao', 'vr_operacao_tributacao',
            'bc_icms_proprio', 'vr_icms_proprio',
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
            'vr_custo_comercial'
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
                    dados[campo] += getattr(item, campo, D(0))

                    if 'produtos_' + campo in dados:
                        if getattr(item, 'tipo_item', False) == 'P':
                            dados['produtos_' + campo] += \
                                getattr(item, campo, D(0))

                    if 'servicos_' + campo in dados:
                        if getattr(item, 'tipo_item', False) == 'S':
                            dados['servicos_' + campo] += \
                                getattr(item, campo, D(0))

                    if 'mensalidades_' + campo in dados:
                        if getattr(item, 'tipo_item', False) == 'M':
                            dados['mensalidades_' + campo] += \
                                getattr(item, campo, D(0))

            documento.update(dados)

    def _inverse_rateio_campo_total(self, campo, tipo_item=None):
        self.ensure_one()

        if not getattr(self, campo, False):
            return

        for item in self.item_ids:
            if tipo_item is None:
                item.write({
                    campo: calc_price_ratio(
                        item.vr_nf,
                        getattr(item.documento_id, campo, 0),
                        item.documento_id.vr_nf),
                })

            elif getattr(item, 'tipo_item', False) == tipo_item:
                if tipo_item == 'P':
                    campo_rateio = 'produtos_' + campo
                elif tipo_item == 'S':
                    campo_rateio = 'servicos_' + campo
                elif tipo_item == 'M':
                    campo_rateio = 'mensalidades_' + campo

                item.write({
                    campo: calc_price_ratio(
                        item.vr_nf,
                        getattr(item.documento_id, campo_rateio, 0),
                        item.documento_id.vr_nf),
                })
            item.calcula_impostos()

    def _inverse_rateio_vr_frete(self):
        self.ensure_one()
        self._inverse_rateio_campo_total('vr_frete')

    def _inverse_rateio_vr_seguro(self):
        self.ensure_one()
        self._inverse_rateio_campo_total('vr_seguro')

    def _inverse_rateio_vr_outras(self):
        self.ensure_one()
        self._inverse_rateio_campo_total('vr_outras')

    def _inverse_rateio_vr_desconto(self):
        self.ensure_one()
        self._inverse_rateio_campo_total('vr_desconto')

    @api.onchange('condicao_pagamento_id')
    def _onchange_condicao_pagamento_id(self):
        self.ensure_one()
        self.payment_term_id = self.condicao_pagamento_id

    @api.onchange('participante_id')
    def _onchange_participante_id(self):
        self.ensure_one()
        self.partner_id = self.participante_id.partner_id

    @api.multi
    def _prepare_sped(self, operacao_id):
        """
        Prepare the dict of values to create the new fiscal for an invoice.

        This method may be overridden to implement custom fiscal generation

        (making sure to call super() to establish a clean extension chain).
        """
        self.ensure_one()
        infcomplementar = self.comment if 'comment' in self._fields \
            else self.note or ''

        sped_vals = {
            'empresa_id': self.sped_empresa_id.id,
            'operacao_id': operacao_id.id,  # FIXME
            'participante_id': self.sped_participante_id.id,
            'payment_term_id': self.condicao_pagamento_id and \
                               self.condicao_pagamento_id.id or False,
            'modelo': operacao_id.modelo,
            'emissao': operacao_id.emissao,
            'natureza_operacao_id': operacao_id.natureza_operacao_id.id,
            'infcomplementar': infcomplementar,
            'journal_id': self.journal_id.id if 'journal_id' in \
                                                self._fields else False,
            'serie': operacao_id.serie,
            # 'duplicata_ids': ,
            # 'pagamento_ids': ,
            # 'transportadora_id': ,
            # 'volume_ids': ,
            # 'name': self.client_order_ref or '',
            # 'origin': self.name,
            # 'type': 'out_invoice',
            # 'account_id':
            #   self.partner_invoice_id.property_account_receivable_id.id,
            # 'partner_shipping_id': self.partner_shipping_id.id,k
            # 'user_id': self.user_id and self.user_id.id,
            # 'team_id': self.team_id.id
        }

        return sped_vals
