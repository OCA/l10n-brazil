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

from .sped_calculo_imposto import SpedCalculoImposto

class SpedCalculoImpostoProdutoServico(SpedCalculoImposto):
    _abstract = False

    #
    # Totais dos itens que são produtos
    #
    produtos_vr_produtos = fields.Monetary(
        string='Valor dos produtos',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_vr_produtos_tributacao = fields.Monetary(
        string='Valor dos produtos para tributação',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_vr_frete = fields.Monetary(
        string='Valor do frete',
        compute='_compute_soma_itens',
        store=True,
        inverse='_inverse_rateio_produtos_vr_frete',
    )
    produtos_vr_seguro = fields.Monetary(
        string='Valor do seguro',
        compute='_compute_soma_itens',
        store=True,
        inverse='_inverse_rateio_produtos_vr_seguro',
    )
    produtos_vr_desconto = fields.Monetary(
        string='Valor do desconto',
        compute='_compute_soma_itens',
        store=True,
        inverse='_inverse_rateio_produtos_vr_desconto',
    )
    produtos_vr_outras = fields.Monetary(
        string='Outras despesas acessórias',
        compute='_compute_soma_itens',
        store=True,
        inverse='_inverse_rateio_produtos_vr_outras',
    )
    produtos_vr_operacao = fields.Monetary(
        string='Valor da operação',
        compute='_compute_soma_itens',
        store=True
    )
    produtos_vr_operacao_tributacao = fields.Monetary(
        string='Valor da operação para tributação',
        compute='_compute_soma_itens',
        store=True
    )
    # ICMS próprio
    produtos_bc_icms_proprio = fields.Monetary(
        string='Base do ICMS próprio',
        compute='_compute_soma_itens',
        store=True
    )
    produtos_vr_icms_proprio = fields.Monetary(
        string='Valor do ICMS próprio',
        compute='_compute_soma_itens',
        store=True
    )
    # ICMS SIMPLES
    produtos_vr_icms_sn = fields.Monetary(
        string='Valor do crédito de ICMS - SIMPLES Nacional',
        compute='_compute_soma_itens',
        store=True
    )
    produtos_vr_simples = fields.Monetary(
        string='Valor do SIMPLES Nacional',
        compute='_compute_soma_itens',
        store=True,
    )
    # ICMS ST
    produtos_bc_icms_st = fields.Monetary(
        string='Base do ICMS ST',
        compute='_compute_soma_itens',
        store=True
    )
    produtos_vr_icms_st = fields.Monetary(
        string='Valor do ICMS ST',
        compute='_compute_soma_itens',
        store=True,
    )
    # ICMS ST retido
    produtos_bc_icms_st_retido = fields.Monetary(
        string='Base do ICMS retido anteriormente por '
               'substituição tributária',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_vr_icms_st_retido = fields.Monetary(
        string='Valor do ICMS retido anteriormente por '
               'substituição tributária',
        compute='_compute_soma_itens',
        store=True,
    )
    # IPI
    produtos_bc_ipi = fields.Monetary(
        string='Base do IPI',
        compute='_compute_soma_itens',
        store=True
    )
    produtos_vr_ipi = fields.Monetary(
        string='Valor do IPI',
        compute='_compute_soma_itens',
        store=True,
    )
    # Imposto de importação
    produtos_bc_ii = fields.Monetary(
        string='Base do imposto de importação',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_vr_despesas_aduaneiras = fields.Monetary(
        string='Despesas aduaneiras',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_vr_ii = fields.Monetary(
        string='Valor do imposto de importação',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_vr_iof = fields.Monetary(
        string='Valor do IOF',
        compute='_compute_soma_itens',
        store=True,
    )
    # PIS e COFINS
    produtos_bc_pis_proprio = fields.Monetary(
        string='Base do PIS próprio',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_vr_pis_proprio = fields.Monetary(
        string='Valor do PIS próprio',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_bc_cofins_proprio = fields.Monetary(
        string='Base da COFINS própria',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_vr_cofins_proprio = fields.Monetary(
        string='Valor do COFINS própria',
        compute='_compute_soma_itens',
        store=True,
    )
    # #
    # # Totais dos itens (grupo ISS)
    # #
    # # ISS
    # produtos_bc_iss = fields.Monetary(
    #     string='Base do ISS',
    #     compute='_compute_soma_itens',
    #     store=True,
    # )
    # produtos_vr_iss = fields.Monetary(
    #     string='Valor do ISS',
    #     compute='_compute_soma_itens',
    #     store=True,
    # )
    # Total da NF e da fatura (podem ser diferentes no caso de operação
    # triangular)
    produtos_vr_nf = fields.Monetary(
        string='Valor da NF',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_vr_fatura = fields.Monetary(
        string='Valor da fatura',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_vr_ibpt = fields.Monetary(
        string='Valor IBPT',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_bc_inss_retido = fields.Monetary(
        string='Base do INSS',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_vr_inss_retido = fields.Monetary(
        string='Valor do INSS',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_vr_custo_comercial = fields.Monetary(
        string='Custo comercial',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_vr_difal = fields.Monetary(
        string='Valor do diferencial de alíquota ICMS próprio',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_vr_icms_estado_origem = fields.Monetary(
        string='Valor do ICMS para o estado origem',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_vr_icms_estado_destino = fields.Monetary(
        string='Valor do ICMS para o estado destino',
        compute='_compute_soma_itens',
        store=True,
    )
    produtos_vr_fcp = fields.Monetary(
        string='Valor do fundo de combate à pobreza',
        compute='_compute_soma_itens',
        store=True,
    )

    #
    # Totais dos itens que são serviços
    #
    servicos_vr_produtos = fields.Monetary(
        string='Valor dos serviços',
        compute='_compute_soma_itens',
        store=True,
    )
    servicos_vr_produtos_tributacao = fields.Monetary(
        string='Valor dos serviços para tributação',
        compute='_compute_soma_itens',
        store=True,
    )
    # servicos_vr_frete = fields.Monetary(
    #     string='Valor do frete',
    #     compute='_compute_soma_itens',
    #     store=True,
    #     inverse='_inverse_rateio_servicos_vr_frete',
    # )
    # servicos_vr_seguro = fields.Monetary(
    #     string='Valor do seguro',
    #     compute='_compute_soma_itens',
    #     store=True,
    #     inverse='_inverse_rateio_servicos_vr_seguro',
    # )
    servicos_vr_desconto = fields.Monetary(
        string='Valor do desconto',
        compute='_compute_soma_itens',
        store=True,
        inverse='_inverse_rateio_servicos_vr_desconto',
    )
    servicos_vr_outras = fields.Monetary(
        string='Outras despesas acessórias',
        compute='_compute_soma_itens',
        store=True,
        inverse='_inverse_rateio_servicos_vr_outras',
    )
    servicos_vr_operacao = fields.Monetary(
        string='Valor da operação',
        compute='_compute_soma_itens',
        store=True
    )
    servicos_vr_operacao_tributacao = fields.Monetary(
        string='Valor da operação para tributação',
        compute='_compute_soma_itens',
        store=True
    )
    # # ICMS próprio
    # servicos_bc_icms_proprio = fields.Monetary(
    #     string='Base do ICMS próprio',
    #     compute='_compute_soma_itens',
    #     store=True
    # )
    # servicos_vr_icms_proprio = fields.Monetary(
    #     string='Valor do ICMS próprio',
    #     compute='_compute_soma_itens',
    #     store=True
    # )
    # # ICMS SIMPLES
    # servicos_vr_icms_sn = fields.Monetary(
    #     string='Valor do crédito de ICMS - SIMPLES Nacional',
    #     compute='_compute_soma_itens',
    #     store=True
    # )
    servicos_vr_simples = fields.Monetary(
        string='Valor do SIMPLES Nacional',
        compute='_compute_soma_itens',
        store=True,
    )
    # # ICMS ST
    # servicos_bc_icms_st = fields.Monetary(
    #     string='Base do ICMS ST',
    #     compute='_compute_soma_itens',
    #     store=True
    # )
    # servicos_vr_icms_st = fields.Monetary(
    #     string='Valor do ICMS ST',
    #     compute='_compute_soma_itens',
    #     store=True,
    # )
    # # ICMS ST retido
    # servicos_bc_icms_st_retido = fields.Monetary(
    #     string='Base do ICMS retido anteriormente por '
    #            'substituição tributária',
    #     compute='_compute_soma_itens',
    #     store=True,
    # )
    # servicos_vr_icms_st_retido = fields.Monetary(
    #     string='Valor do ICMS retido anteriormente por '
    #            'substituição tributária',
    #     compute='_compute_soma_itens',
    #     store=True,
    # )
    # # IPI
    # servicos_bc_ipi = fields.Monetary(
    #     string='Base do IPI',
    #     compute='_compute_soma_itens',
    #     store=True
    # )
    # servicos_vr_ipi = fields.Monetary(
    #     string='Valor do IPI',
    #     compute='_compute_soma_itens',
    #     store=True,
    # )
    # # Imposto de importação
    # servicos_bc_ii = fields.Monetary(
    #     string='Base do imposto de importação',
    #     compute='_compute_soma_itens',
    #     store=True,
    # )
    # servicos_vr_despesas_aduaneiras = fields.Monetary(
    #     string='Despesas aduaneiras',
    #     compute='_compute_soma_itens',
    #     store=True,
    # )
    # servicos_vr_ii = fields.Monetary(
    #     string='Valor do imposto de importação',
    #     compute='_compute_soma_itens',
    #     store=True,
    # )
    # servicos_vr_iof = fields.Monetary(
    #     string='Valor do IOF',
    #     compute='_compute_soma_itens',
    #     store=True,
    # )
    # PIS e COFINS
    servicos_bc_pis_proprio = fields.Monetary(
        string='Base do PIS próprio',
        compute='_compute_soma_itens',
        store=True,
    )
    servicos_vr_pis_proprio = fields.Monetary(
        string='Valor do PIS próprio',
        compute='_compute_soma_itens',
        store=True,
    )
    servicos_bc_cofins_proprio = fields.Monetary(
        string='Base da COFINS própria',
        compute='_compute_soma_itens',
        store=True,
    )
    servicos_vr_cofins_proprio = fields.Monetary(
        string='Valor do COFINS própria',
        compute='_compute_soma_itens',
        store=True,
    )
    #
    # Totais dos itens (grupo ISS)
    #
    # ISS
    servicos_bc_iss = fields.Monetary(
        string='Base do ISS',
        compute='_compute_soma_itens',
        store=True,
    )
    servicos_vr_iss = fields.Monetary(
        string='Valor do ISS',
        compute='_compute_soma_itens',
        store=True,
    )
    # Total da NF e da fatura (podem ser diferentes no caso de operação
    # triangular)
    servicos_vr_nf = fields.Monetary(
        string='Valor da NF',
        compute='_compute_soma_itens',
        store=True,
    )
    servicos_vr_fatura = fields.Monetary(
        string='Valor da fatura',
        compute='_compute_soma_itens',
        store=True,
    )
    servicos_vr_ibpt = fields.Monetary(
        string='Valor IBPT',
        compute='_compute_soma_itens',
        store=True,
    )
    servicos_bc_inss_retido = fields.Monetary(
        string='Base do INSS',
        compute='_compute_soma_itens',
        store=True,
    )
    servicos_vr_inss_retido = fields.Monetary(
        string='Valor do INSS',
        compute='_compute_soma_itens',
        store=True,
    )
    servicos_vr_custo_comercial = fields.Monetary(
        string='Custo comercial',
        compute='_compute_soma_itens',
        store=True,
    )
    # servicos_vr_difal = fields.Monetary(
    #     string='Valor do diferencial de alíquota ICMS próprio',
    #     compute='_compute_soma_itens',
    #     store=True,
    # )
    # servicos_vr_icms_estado_origem = fields.Monetary(
    #     string='Valor do ICMS para o estado origem',
    #     compute='_compute_soma_itens',
    #     store=True,
    # )
    # servicos_vr_icms_estado_destino = fields.Monetary(
    #     string='Valor do ICMS para o estado destino',
    #     compute='_compute_soma_itens',
    #     store=True,
    # )
    # servicos_vr_fcp = fields.Monetary(
    #     string='Valor do fundo de combate à pobreza',
    #     compute='_compute_soma_itens',
    #     store=True,
    # )


    def _inverse_rateio_produtos_vr_frete(self):
        self.ensure_one()
        self._inverse_rateio_campo_total('vr_frete', tipo_item='P')

    def _inverse_rateio_produtos_vr_seguro(self):
        self.ensure_one()
        self._inverse_rateio_campo_total('vr_seguro', tipo_item='P')

    def _inverse_rateio_produtos_vr_outras(self):
        self.ensure_one()
        self._inverse_rateio_campo_total('vr_outras', tipo_item='P')

    def _inverse_rateio_produtos_vr_desconto(self):
        self.ensure_one()
        self._inverse_rateio_campo_total('vr_desconto', tipo_item='P')

    # def _inverse_rateio_servicos_vr_frete(self):
    #     self.ensure_one()
    #     self._inverse_rateio_campo_total('vr_frete', tipo_item='S')
    #
    # def _inverse_rateio_servicos_vr_seguro(self):
    #     self.ensure_one()
    #     self._inverse_rateio_campo_total('vr_seguro', tipo_item='S')

    def _inverse_rateio_servicos_vr_outras(self):
        self.ensure_one()
        self._inverse_rateio_campo_total('vr_outras', tipo_item='S')

    def _inverse_rateio_servicos_vr_desconto(self):
        self.ensure_one()
        self._inverse_rateio_campo_total('vr_desconto', tipo_item='S')
