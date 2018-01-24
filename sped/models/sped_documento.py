# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# Copyright 2017 KMEE INFORMATICA LTDA
#   Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models, tools,  _
from odoo.exceptions import ValidationError
from odoo.addons.sped_imposto.models.sped_calculo_imposto import SpedCalculoImposto

from odoo.addons.l10n_br_base.constante_tributaria import *
from openerp.addons.sped_imposto.models.sped_calculo_imposto import \
    SpedCalculoImposto

_logger = logging.getLogger(__name__)

try:
    from pybrasil.data import parse_datetime, data_hora_horario_brasilia, \
        formata_data
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.valor import formata_valor

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumento(SpedCalculoImposto, models.Model):
    _name = b'sped.documento'
    _description = 'Documentos Fiscais'
    _inherit = ['mail.thread']
    _order = 'emissao, modelo, data_entrada_saida desc, data_emissao desc,' + \
             ' serie, numero desc'
    _rec_name = 'descricao'

    descricao = fields.Char(
        string='Documento Fiscal',
        compute='_compute_descricao',
    )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        ondelete='restrict',
        default=lambda self:
        self.env['sped.empresa']._empresa_ativa('sped.empresa')
    )
    empresa_cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        size=18,
        related='empresa_id.cnpj_cpf',
        readonly=True,
    )
    emissao = fields.Selection(
        selection=TIPO_EMISSAO,
        string='Tipo de emissão',
        index=True,
    )
    modelo = fields.Selection(
        selection=MODELO_FISCAL,
        string='Modelo',
        index=True,
    )
    data_hora_emissao = fields.Datetime(
        string='Data de emissão',
        index=True,
        default=fields.Datetime.now,
    )
    data_hora_entrada_saida = fields.Datetime(
        string='Data de entrada/saída',
        index=True,
        default=fields.Datetime.now,
    )
    data_emissao = fields.Date(
        string='Data de emissão',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
        copy=False,
    )
    hora_emissao = fields.Char(
        string='Hora de emissão',
        size=8,
        compute='_compute_data_hora_separadas',
        store=True,
        copy=False,
    )
    data_entrada_saida = fields.Date(
        string='Data de entrada/saída',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
        copy=False,
    )
    hora_entrada_saida = fields.Char(
        string='Hora de entrada/saída',
        size=8,
        compute='_compute_data_hora_separadas',
        store=True,
        copy=False,
    )
    serie = fields.Char(
        string='Série',
        size=3,
        index=True,
        copy=False,
    )
    numero = fields.Float(
        string='Número',
        index=True,
        digits=(18, 0),
        copy=False,
    )
    entrada_saida = fields.Selection(
        selection=ENTRADA_SAIDA,
        string='Entrada/Saída',
        index=True,
        default=ENTRADA_SAIDA_SAIDA,
    )
    situacao_nfe = fields.Selection(
        selection=SITUACAO_NFE,
        string='Situação NF-e',
        default=SITUACAO_NFE_EM_DIGITACAO,
        copy=False,
    )
    situacao_fiscal = fields.Selection(
        selection=SITUACAO_FISCAL,
        string='Situação fiscal',
        index=True,
        default=SITUACAO_FISCAL_REGULAR,
    )
    ambiente_nfe = fields.Selection(
        selection=AMBIENTE_NFE,
        string='Ambiente da NF-e',
        index=True,
        default=AMBIENTE_NFE_HOMOLOGACAO,
    )
    tipo_emissao_nfe = fields.Selection(
        selection=TIPO_EMISSAO_NFE,
        string='Tipo de emissão da NF-e',
        default=TIPO_EMISSAO_NFE_NORMAL,
    )
    ie_st = fields.Char(
        string='IE do substituto tributário',
        size=14,
    )
    municipio_fato_gerador_id = fields.Many2one(
        comodel_name='sped.municipio',
        string='Município do fato gerador',
    )
    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação',
        ondelete='restrict',
    )
    operacao_subsequente_ids = fields.One2many(
        comodel_name='sped.operacao.subsequente',
        related='operacao_id.operacao_subsequente_ids',
        readonly=True,
    )
    #
    # Campos da operação
    #
    regime_tributario = fields.Selection(
        selection=REGIME_TRIBUTARIO,
        string='Regime tributário',
    )
    ind_forma_pagamento = fields.Selection(
        selection=IND_FORMA_PAGAMENTO,
        string='Tipo de pagamento',
        default=IND_FORMA_PAGAMENTO_A_VISTA,
    )
    finalidade_nfe = fields.Selection(
        selection=FINALIDADE_NFE,
        string='Finalidade da NF-e',
        default=FINALIDADE_NFE_NORMAL,
    )
    consumidor_final = fields.Selection(
        selection=TIPO_CONSUMIDOR_FINAL,
        string='Tipo do consumidor',
        default=TIPO_CONSUMIDOR_FINAL_NORMAL,
    )
    presenca_comprador = fields.Selection(
        selection=INDICADOR_PRESENCA_COMPRADOR,
        string='Presença do comprador',
        default=INDICADOR_PRESENCA_COMPRADOR_NAO_SE_APLICA,
    )
    modalidade_frete = fields.Selection(
        selection=MODALIDADE_FRETE,
        string='Modalidade do frete',
        default=MODALIDADE_FRETE_DESTINATARIO_FOB,
    )
    natureza_operacao_id = fields.Many2one(
        comodel_name='sped.natureza.operacao',
        string='Natureza da operação',
        ondelete='restrict',
    )
    infadfisco = fields.Text(
        string='Informações adicionais de interesse do fisco'
    )
    infcomplementar = fields.Text(
        string='Informações complementares'
    )
    deduz_retencao = fields.Boolean(
        string='Deduz retenção do total da NF?',
        default=True
    )
    pis_cofins_retido = fields.Boolean(
        string='PIS-COFINS retidos?'
    )
    al_pis_retido = fields.Monetary(
        string='Alíquota do PIS',
        default=0.65,
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_cofins_retido = fields.Monetary(
        string='Alíquota da COFINS',
        default=3,
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    csll_retido = fields.Boolean(
        string='CSLL retido?',
    )
    al_csll = fields.Monetary(
        string='Alíquota da CSLL',
        default=1,
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    limite_retencao_pis_cofins_csll = fields.Monetary(
        string='Obedecer limite de faturamento para retenção de',
        default=LIMITE_RETENCAO_PIS_COFINS_CSLL,
    )
    irrf_retido = fields.Boolean(
        string='IR retido?',
    )
    irrf_retido_ignora_limite = fields.Boolean(
        string='IR retido ignora limite de R$ 10,00?',
    )
    al_irrf = fields.Monetary(
        string='Alíquota do IR',
        default=1,
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    inss_retido = fields.Boolean(
        string='INSS retido?',
        index=True,
    )
    al_inss_retido = fields.Monetary(
        string='Alíquota do INSS',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_inss = fields.Monetary(
        string='Alíquota do INSS',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    cnae_id = fields.Many2one(
        comodel_name='sped.cnae',
        string='CNAE',
    )
    natureza_tributacao_nfse = fields.Selection(
        selection=NATUREZA_TRIBUTACAO_NFSE,
        string='Natureza da tributação',
    )
    servico_id = fields.Many2one(
        comodel_name='sped.servico',
        string='Serviço',
    )
    cst_iss = fields.Selection(
        selection=ST_ISS,
        string='CST ISS',
    )
    #
    # Destinatário/Remetente
    #
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Destinatário/Remetente',
        ondelete='restrict',
    )
    participante_cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        size=18,
        related='participante_id.cnpj_cpf',
        readonly=True,
    )
    participante_tipo_pessoa = fields.Char(
        string='Tipo pessoa',
        size=1,
        related='participante_id.tipo_pessoa',
        readonly=True,
    )
    participante_razao_social = fields.Char(
        string='Razão Social',
        size=60,
        related='participante_id.razao_social',
        readonly=True,
    )
    participante_fantasia = fields.Char(
        string='Fantasia',
        size=60,
        related='participante_id.fantasia',
        readonly=True,
    )
    participante_endereco = fields.Char(
        string='Endereço',
        size=60,
        related='participante_id.endereco',
        readonly=True,
    )
    participante_numero = fields.Char(
        string='Número',
        size=60,
        related='participante_id.numero',
        readonly=True,
    )
    participante_complemento = fields.Char(
        string='Complemento',
        size=60,
        related='participante_id.complemento',
        readonly=True,
    )
    participante_bairro = fields.Char(
        string='Bairro',
        size=60,
        related='participante_id.bairro',
        readonly=True,
    )
    participante_municipio_id = fields.Many2one(
        comodel_name='sped.municipio',
        string='Município',
        related='participante_id.municipio_id',
        readonly=True,
    )
    participante_cidade = fields.Char(
        string='Município',
        related='participante_id.cidade',
        readonly=True,
    )
    participante_estado = fields.Char(
        string='Estado',
        related='participante_id.estado',
        readonly=True,
    )
    participante_cep = fields.Char(
        string='CEP',
        size=9,
        related='participante_id.cep',
        readonly=True,
    )
    #
    # Telefone e email para a emissão da NF-e
    #
    participante_fone = fields.Char(
        string='Fone',
        size=18,
        related='participante_id.fone',
        readonly=True,
    )
    participante_fone_comercial = fields.Char(
        string='Fone Comercial',
        size=18,
        related='participante_id.fone_comercial',
        readonly=True,
    )
    participante_celular = fields.Char(
        string='Celular',
        size=18,
        related='participante_id.celular',
        readonly=True,
    )
    participante_email = fields.Char(
        string='Email',
        size=60,
        related='participante_id.email',
        readonly=True,
    )
    #
    # Inscrições e documentos
    #
    participante_contribuinte = fields.Selection(
        selection=IE_DESTINATARIO,
        string='Contribuinte',
        default='2',
        related='participante_id.contribuinte',
        readonly=True,
    )
    participante_ie = fields.Char(
        string='Inscrição estadual',
        size=18,
        related='participante_id.ie',
        readonly=True,
    )
    participante_eh_orgao_publico = fields.Boolean(
        string='É órgão público?',
        related='participante_id.eh_orgao_publico',
        readonly=True,
    )

    #
    # Chave e validação da chave
    #
    chave = fields.Char(
        string='Chave',
        size=44,
        copy=False,
    )
    #
    # Duplicatas e pagamentos
    #
    condicao_pagamento_id = fields.Many2one(
        comodel_name='account.payment.term',
        string='Condição de pagamento',
        ondelete='restrict',
        domain=[('forma_pagamento', '!=', False)],
    )
    duplicata_ids = fields.One2many(
        comodel_name='sped.documento.duplicata',
        inverse_name='documento_id',
        string='Duplicatas',
    )
    pagamento_ids = fields.One2many(
        comodel_name='sped.documento.pagamento',
        inverse_name='documento_id',
        string='Pagamentos',
    )

    #
    # Endereços de entrega e retirada
    #
    endereco_retirada_id = fields.Many2one(
        comodel_name='sped.endereco',
        string='Endereço de retirada',
        ondelete='restrict'
    )
    endereco_entrega_id = fields.Many2one(
        comodel_name='sped.endereco',
        string='Endereço de entrega',
        ondelete='restrict'
    )

    #
    # Transporte
    #
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
    reboque_1_id = fields.Many2one(
        comodel_name='sped.veiculo',
        string='Reboque 1',
        ondelete='restrict',
    )
    reboque_2_id = fields.Many2one(
        comodel_name='sped.veiculo',
        string='Reboque 2',
        ondelete='restrict',
    )
    reboque_3_id = fields.Many2one(
        comodel_name='sped.veiculo',
        string='Reboque 3',
        ondelete='restrict',
    )
    reboque_4_id = fields.Many2one(
        comodel_name='sped.veiculo',
        string='Reboque 4',
        ondelete='restrict',
    )
    reboque_5_id = fields.Many2one(
        comodel_name='sped.veiculo',
        string='Reboque 5',
        ondelete='restrict',
    )

    volume_ids = fields.One2many(
        comodel_name='sped.documento.volume',
        inverse_name='documento_id',
        string='Volumes'
    )

    #
    # Exportação
    #
    exportacao_estado_embarque_id = fields.Many2one(
        comodel_name='sped.estado',
        string='Estado do embarque',
        ondelete='restrict',
    )
    exportacao_local_embarque = fields.Char(
        string='Local do embarque',
        size=60,
    )

    #
    # Compras públicas
    #
    compra_nota_empenho = fields.Char(
        string='Identificação da nota de empenho (compra pública)',
        size=17,
    )
    compra_pedido = fields.Char(
        string='Pedido (compra pública)',
        size=60,
    )
    compra_contrato = fields.Char(
        string='Contrato (compra pública)',
        size=60,
    )
    #
    # Totais dos itens
    #

    # Valor total dos produtos
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
    )
    vr_seguro = fields.Monetary(
        string='Valor do seguro',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_desconto = fields.Monetary(
        string='Valor do desconto',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_outras = fields.Monetary(
        string='Outras despesas acessórias',
        compute='_compute_soma_itens',
        store=True,
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
    ###
    # Retenções de tributos (órgãos públicos, substitutos tributários etc.)
    ###
    # 'vr_operacao_pis_cofins_csll = CampoDinheiro(
    # 'Base da retenção do PIS-COFINS e CSLL'),

    # PIS e COFINS
    # 'pis_cofins_retido = fields.boolean('PIS-COFINS retidos?'),
    # 'al_pis_retido = CampoPorcentagem('Alíquota do PIS retido'),
    # 'vr_pis_retido = CampoDinheiro('PIS retido'),
    # 'al_cofins_retido = CampoPorcentagem('Alíquota da COFINS retida'),
    # 'vr_cofins_retido = CampoDinheiro('COFINS retida'),

    # Contribuição social sobre lucro líquido
    # 'csll_retido = fields.boolean('CSLL retida?'),
    # 'al_csll = CampoPorcentagem('Alíquota da CSLL'),
    # 'vr_csll = CampoDinheiro('CSLL retida'),
    # 'bc_csll_propria = CampoDinheiro('Base da CSLL própria'),
    # 'al_csll_propria = CampoPorcentagem('Alíquota da CSLL própria'),
    # 'vr_csll_propria = CampoDinheiro('CSLL própria'),

    # IRRF
    # 'irrf_retido = fields.boolean('IR retido?'),
    # 'bc_irrf = CampoDinheiro('Base do IRRF'),
    # 'al_irrf = CampoPorcentagem('Alíquota do IRRF'),
    # 'vr_irrf = CampoDinheiro('Valor do IRRF'),
    # 'bc_irpj_proprio = CampoDinheiro('Valor do IRPJ próprio'),
    # 'al_irpj_proprio = CampoPorcentagem('Alíquota do IRPJ próprio'),
    # 'vr_irpj_proprio = CampoDinheiro('Valor do IRPJ próprio'),

    # ISS
    # 'iss_retido = fields.boolean('ISS retido?'),
    # 'bc_iss_retido = CampoDinheiro('Base do ISS'),
    # 'vr_iss_retido = CampoDinheiro('Valor do ISS'),

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

    item_ids = fields.One2many(
        comodel_name='sped.documento.item',
        inverse_name='documento_id',
        string='Itens',
        copy=True,
    )
    produto_id = fields.Many2one(
        comodel_name='sped.produto',
        string='Produto/Serviço',
        related='item_ids.produto_id',
        readonly=True,
    )
    cfop_id = fields.Many2one(
        comodel_name='sped.cfop',
        string='CFOP',
        related='item_ids.cfop_id',
        readonly=True,
    )
    ncm_id = fields.Many2one(
        comodel_name='sped.ncm',
        string='NCM',
        related='produto_id.ncm_id',
        readonly=True,
    )
    cest_id = fields.Many2one(
        comodel_name='sped.cest',
        string='CEST',
        related='produto_id.cest_id',
        readonly=True,
    )
    #
    # Outras informações
    #
    eh_compra = fields.Boolean(
        string='É compra?',
        compute='_compute_eh_compra_venda',
    )
    eh_venda = fields.Boolean(
        string='É venda?',
        compute='_compute_eh_compra_venda',
    )
    eh_devolucao_compra = fields.Boolean(
        string='É devolução de compra?',
        compute='_compute_eh_compra_venda',
    )
    eh_devolucao_venda = fields.Boolean(
        string='É devolução de venda?',
        compute='_compute_eh_compra_venda',
    )
    permite_alteracao = fields.Boolean(
        string='Permite alteração?',
        compute='_compute_permite_alteracao',
    )
    permite_cancelamento = fields.Boolean(
        string='Permite cancelamento?',
        compute='_compute_permite_cancelamento',
    )
    permite_inutilizacao = fields.Boolean(
        string='Permite inutilização?',
        compute='_compute_permite_inutilizacao',
    )
    importado_xml = fields.Boolean(
        string='Importado de XML?',
    )
    documento_referenciado_ids = fields.One2many(
        comodel_name='sped.documento.referenciado',
        inverse_name='documento_id',
        string='Documentos Referenciados',
    )
    #
    # O campo acima é o documento referenciado que é enviado no XML
    #
    #
    # Já os campos abaixos representam relacionamentos entre os documentos que nem sempre são permitidos pelo sefaz:
    #
    #       Por exemplo uma nota de transferencia gerada a partir de outra operação.
    #
    documento_origem_ids = fields.One2many(
        comodel_name='sped.documento.subsequente',
        string="Documento Original",
        inverse_name='documento_subsequente_id',
        readonly=True,
        copy=False,
    )
    # display_name = fields.Char(
    #     compute='_compute_display_name',
    #     store=True,
    #     index=True,
    # )

    documentos_subsequentes_gerados = fields.Boolean(
        string='Documentos Subsequentes gerados?',
        compute='_compute_documentos_subsequentes_gerados',
        default=False,
    )
    documento_subsequente_ids = fields.One2many(
        comodel_name='sped.documento.subsequente',
        inverse_name='documento_origem_id',
        compute='_compute_documento_subsequente_ids',
    )
    documento_impresso = fields.Boolean(
        string='Impresso',
        readonly=True,
    )

    documento_origem_id = fields.Reference(
        selection="_selection_documento_origem_id",
        string='Documento de Origem',
        help='Documento que originou o sped.documento.',
    )

    @api.model
    @tools.ormcache("self")
    def _selection_documento_origem_id(self):
        """Allow any model; after all, this field is readonly."""
        return [(r.model, r.name) for r in self.env["ir.model"].search([])]

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            if self._context.get('sped_documento_display') == 'completo':
                res.append((record.id, record.descricao))
            else:
                txt = '{nome}/{modelo}/{serie}/{numero}'.format(
                    nome=record.empresa_id.nome,
                    modelo=record.modelo,
                    serie=record.serie,
                    numero=formata_valor(record.numero, casas_decimais=0),
                )
                res.append((record.id, txt))
        return res

    @api.depends('emissao', 'entrada_saida', 'modelo', 'serie', 'numero',
                 'data_emissao', 'participante_id')
    def _compute_descricao(self):
        for documento in self:
            txt = TIPO_EMISSAO_DICT[documento.emissao]

            if documento.emissao == TIPO_EMISSAO_PROPRIA:
                txt += ' - ' + ENTRADA_SAIDA_DICT[documento.entrada_saida]

            txt += ' - ' + documento.modelo
            txt += ' - ' + (documento.serie or '')
            txt += ' - ' + formata_valor(documento.numero, casas_decimais=0)
            txt += ' - ' + formata_data(documento.data_emissao)

            if not documento.participante_id.cnpj_cpf:
                txt += ' - Consumidor não identificado'

            elif documento.participante_id.razao_social:
                txt += ' - ' + documento.participante_id.razao_social
                txt += ' - ' + documento.participante_id.cnpj_cpf
            else:
                txt += ' - ' + documento.participante_id.nome
                txt += ' - ' + documento.participante_id.cnpj_cpf

            documento.descricao = txt

    @api.depends('modelo', 'emissao', 'importado_xml')
    def _compute_permite_alteracao(self):
        for documento in self:
            documento.permite_alteracao = documento.importado_xml

    @api.depends('modelo', 'emissao', 'importado_xml')
    def _compute_permite_cancelamento(self):
        for documento in self:
            documento.permite_cancelamento = True
            # not documento.importado_xml

    @api.depends('modelo', 'emissao', 'importado_xml')
    def _compute_permite_inutilizacao(self):
        for documento in self:
            documento.permite_inutilizacao = not documento.importado_xml

    @api.depends('data_hora_emissao', 'data_hora_entrada_saida')
    def _compute_data_hora_separadas(self):
        for documento in self:
            data, hora = self._separa_data_hora(documento.data_hora_emissao)
            documento.data_emissao = data
            documento.hora_emissao = hora

            data, hora = \
                self._separa_data_hora(documento.data_hora_entrada_saida)
            documento.data_entrada_saida = data
            documento.hora_entrada_saida = hora

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

            for item in documento.item_ids:
                for campo in CAMPOS_SOMA_ITENS:
                    dados[campo] += getattr(item, campo, D(0))

            documento.update(dados)

    @api.depends('item_ids')
    def _compute_eh_compra_venda(self):
        for documento in self:
            if documento.entrada_saida == ENTRADA_SAIDA_ENTRADA:
                self.eh_venda = False
                self.eh_devolucao_compra = False

                for item in documento.item_ids:
                    if item.cfop_id.eh_compra:
                        self.eh_compra = True
                        self.eh_devolucao_venda = False
                        continue

                    elif item.cfop_id.eh_devolucao_venda:
                        self.eh_compra = False
                        self.eh_devolucao_venda = True
                        continue

            else:
                self.eh_compra = False
                self.eh_devolucao_venda = False

                for item in documento.item_ids:
                    if item.cfop_id.eh_venda:
                        self.eh_venda = True
                        self.eh_devolucao_compra = False
                        continue

                    elif item.cfop_id.eh_devolucao_compra:
                        self.eh_venda = False
                        self.eh_devolucao_compra = True
                        continue

    def _serie_padrao_nfe(self, empresa, ambiente_nfe, tipo_emissao_nfe):
        if tipo_emissao_nfe == TIPO_EMISSAO_NFE_NORMAL:
            if ambiente_nfe == AMBIENTE_NFE_PRODUCAO:
                serie = empresa.serie_nfe_producao
            else:
                serie = empresa.serie_nfe_homologacao

        else:
            if ambiente_nfe == AMBIENTE_NFE_PRODUCAO:
                serie = empresa.serie_nfe_contingencia_producao
            else:
                serie = empresa.serie_nfe_contingencia_homologacao

        return serie

    def _serie_padrao_nfce(self, empresa, ambiente_nfce, tipo_emissao_nfce):
        if tipo_emissao_nfce == TIPO_EMISSAO_NFE_NORMAL:
            if ambiente_nfce == AMBIENTE_NFE_PRODUCAO:
                serie = empresa.serie_nfce_producao
            else:
                serie = empresa.serie_nfce_homologacao

        else:
            if ambiente_nfce == AMBIENTE_NFE_PRODUCAO:
                serie = empresa.serie_nfce_contingencia_producao
            else:
                serie = empresa.serie_nfce_contingencia_homologacao

        return serie

    @api.onchange('empresa_id', 'modelo', 'emissao')
    def _onchange_empresa_id(self):
        res = {}
        valores = {}
        res['value'] = valores

        if not self.empresa_id:
            return res

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        if self.modelo not in (
                MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE, MODELO_FISCAL_NFSE):
            return res

        if self.modelo == MODELO_FISCAL_NFE:
            valores['ambiente_nfe'] = self.empresa_id.ambiente_nfe
            valores['tipo_emissao_nfe'] = self.empresa_id.tipo_emissao_nfe
            valores['serie'] = self._serie_padrao_nfe(
                self.empresa_id,
                self.empresa_id.ambiente_nfe,
                self.empresa_id.tipo_emissao_nfe
            )
            #if self.empresa_id.tipo_emissao_nfe == TIPO_EMISSAO_NFE_NORMAL:
                #if self.empresa_id.ambiente_nfe == AMBIENTE_NFE_PRODUCAO:
                    #valores['serie'] = self.empresa_id.serie_nfe_producao
                #else:
                    #valores['serie'] = self.empresa_id.serie_nfe_homologacao

            #else:
                #if self.empresa_id.ambiente_nfe == AMBIENTE_NFE_PRODUCAO:
                    #valores['serie'] = (
                        #self.empresa_id.serie_nfe_contingencia_producao
                    #)
                #else:
                    #valores['serie'] = (
                        #self.empresa_id.serie_nfe_contingencia_homologacao
                    #)

        elif self.modelo == MODELO_FISCAL_NFCE:
            valores['ambiente_nfe'] = self.empresa_id.ambiente_nfce
            valores['tipo_emissao_nfe'] = self.empresa_id.tipo_emissao_nfce
            valores['serie'] = self._serie_padrao_nfce(
                self.empresa_id,
                self.empresa_id.ambiente_nfce,
                self.empresa_id.tipo_emissao_nfce
            )

            #if self.empresa_id.tipo_emissao_nfce == TIPO_EMISSAO_NFE_NORMAL:
                #if self.empresa_id.ambiente_nfce == AMBIENTE_NFE_PRODUCAO:
                    #valores['serie'] = self.empresa_id.serie_nfce_producao
                #else:
                    #valores['serie'] = self.empresa_id.serie_nfce_homologacao

            #else:
                #if self.empresa_id.ambiente_nfce == AMBIENTE_NFE_PRODUCAO:
                    #valores['serie'] = (
                        #self.empresa_id.serie_nfce_contingencia_producao
                    #)
                #else:
                    #valores['serie'] = (
                        #self.empresa_id.serie_nfce_contingencia_homologacao
                    #)

        elif self.modelo == MODELO_FISCAL_NFSE:
            valores['ambiente_nfe'] = self.empresa_id.ambiente_nfse
            valores['tipo_emissao_nfe'] = TIPO_EMISSAO_NFE_NORMAL

            if self.empresa_id.ambiente_nfse == AMBIENTE_NFE_PRODUCAO:
                valores['serie_rps'] = self.empresa_id.serie_rps_producao
            else:
                valores['serie_rps'] = self.empresa_id.serie_rps_homologacao

        return res

    @api.onchange('operacao_id', 'emissao', 'natureza_operacao_id')
    def _onchange_operacao_id(self):
        res = {}
        valores = {}
        res['value'] = valores

        if not self.operacao_id:
            return res

        valores['modelo'] = self.operacao_id.modelo
        valores['emissao'] = self.operacao_id.emissao
        valores['entrada_saida'] = self.operacao_id.entrada_saida

        if self.emissao == TIPO_EMISSAO_PROPRIA:
            if self.operacao_id.natureza_operacao_id:
                valores['natureza_operacao_id'] = \
                    self.operacao_id.natureza_operacao_id.id

            if self.operacao_id.serie:
                valores['serie'] = self.operacao_id.serie

            if self.operacao_id.ambiente_nfe:
                valores['ambiente_nfe'] = self.operacao_id.ambiente_nfe

                if self.ambiente_nfe != self.operacao_id.ambiente_nfe:
                    if not self.operacao_id.serie:
                        if self.modelo == MODELO_FISCAL_NFE:
                            valores['serie'] = self._serie_padrao_nfe(
                                self.empresa_id,
                                valores['ambiente_nfe'],
                                self.tipo_emissao_nfe
                            )
                        elif self.modelo == MODELO_FISCAL_NFCE:
                            valores['serie'] = self._serie_padrao_nfce(
                                self.empresa_id,
                                valores['ambiente_nfe'],
                                self.tipo_emissao_nfe
                            )

            #else:
                #if not self.operacao_id.serie:
                    #if self.modelo == MODELO_FISCAL_NFE:
                        #valores['serie'] = self._serie_padrao_nfe(
                            #self.empresa_id,
                            #self.empresa_id.ambiente_nfe,
                            #self.empresa_id.tipo_emissao_nfe
                        #)
                    #elif self.modelo == MODELO_FISCAL_NFCE:
                        #valores['serie'] = self._serie_padrao_nfce(
                            #self.empresa_id,
                            #self.empresa_id.ambiente_nfce,
                            #self.empresa_id.tipo_emissao_nfce
                        #)

            valores['regime_tributario'] = self.operacao_id.regime_tributario
            valores['ind_forma_pagamento'] = \
                self.operacao_id.ind_forma_pagamento
            if self.operacao_id.condicao_pagamento_id:
                valores['condicao_pagamento_id'] = \
                    self.operacao_id.condicao_pagamento_id.id
            valores['finalidade_nfe'] = self.operacao_id.finalidade_nfe
            valores['modalidade_frete'] = self.operacao_id.modalidade_frete
            valores['infadfisco'] = self.operacao_id.infadfisco

            if not self.operacao_id.calcular_tributacao in (
                    'somente_calcula', 'manual'):
                if valores.get('infcomplementar'):
                    valores['infcomplementar'] = \
                        valores['infcomplementar'] + ' ' + self.operacao_id.infcomplementar
                else:
                    valores['infcomplementar'] = self.operacao_id.infcomplementar

        valores['deduz_retencao'] = self.operacao_id.deduz_retencao
        valores['pis_cofins_retido'] = self.operacao_id.pis_cofins_retido
        valores['al_pis_retido'] = self.operacao_id.al_pis_retido
        valores['al_cofins_retido'] = self.operacao_id.al_cofins_retido
        valores['csll_retido'] = self.operacao_id.csll_retido
        valores['al_csll'] = self.operacao_id.al_csll
        valores['limite_retencao_pis_cofins_csll'] = (
            self.operacao_id.limite_retencao_pis_cofins_csll
        )
        valores['irrf_retido'] = self.operacao_id.irrf_retido
        valores['irrf_retido_ignora_limite'] = (
            self.operacao_id.irrf_retido_ignora_limite
        )
        valores['al_irrf'] = self.operacao_id.al_irrf
        valores['inss_retido'] = self.operacao_id.inss_retido
        valores['consumidor_final'] = self.operacao_id.consumidor_final
        valores['presenca_comprador'] = self.operacao_id.presenca_comprador

        if self.operacao_id.cnae_id:
            valores['cnae_id'] = self.operacao_id.cnae_id.id

        valores['natureza_tributacao_nfse'] = (
            self.operacao_id.natureza_tributacao_nfse
        )

        if self.operacao_id.servico_id:
            valores['servico_id'] = self.operacao_id.servico_id.id

        valores['cst_iss'] = self.operacao_id.cst_iss

        return res

    @api.onchange('empresa_id', 'modelo', 'emissao', 'serie', 'ambiente_nfe')
    def _onchange_serie(self):
        res = {}
        valores = {}
        res['value'] = valores

        if not self.empresa_id:
            return res

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        if self.modelo not in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE):
            return res

        serie = self.serie and self.serie.strip()

        ultimo_numero = self.search([
            ('empresa_id.cnpj_cpf', '=', self.empresa_id.cnpj_cpf),
            ('ambiente_nfe', '=', self.ambiente_nfe),
            ('emissao', '=', self.emissao),
            ('modelo', '=', self.modelo),
            ('serie', '=', serie),
            ('numero', '!=', False),
        ], limit=1, order='numero desc')

        valores['serie'] = serie

        if len(ultimo_numero) == 0:
            valores['numero'] = 1
        else:
            valores['numero'] = ultimo_numero[0].numero + 1

        return res

    @api.onchange('participante_id')
    def _onchange_participante_id(self):
        res = {}
        valores = {}
        res['value'] = valores

        #
        # Quando o tipo da nota for para consumidor normal,
        # mas o participante não é contribuinte, define que ele é consumidor
        # final, exceto em caso de operação com estrangeiros
        #
        if self.consumidor_final == TIPO_CONSUMIDOR_FINAL_NORMAL:
            if self.participante_id.estado != 'EX':
                if self.participante_id.contribuinte == \
                        INDICADOR_IE_DESTINATARIO_CONTRIBUINTE:
                    valores['consumidor_final'] = \
                        TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL

        if self.operacao_id and self.operacao_id.preco_automatico == 'V':
            if self.participante_id.transportadora_id:
                valores['transportadora_id'] = \
                    self.participante_id.transportadora_id.id

            if self.participante_id.condicao_pagamento_id:
                valores['condicao_pagamento_id'] = \
                    self.participante_id.condicao_pagamento_id.id

        return res

    @api.onchange('condicao_pagamento_id', 'vr_fatura', 'vr_nf', 'data_emissao',
                  'duplicata_ids')
    def _onchange_condicao_pagamento_id(self):
        res = {}
        valores = {}
        res['value'] = valores

        if not (self.condicao_pagamento_id and (self.vr_fatura or self.vr_nf) and
                self.data_emissao):
            return res

        valor = D(self.vr_fatura or 0)
        if not valor:
            valor = D(self.vr_nf or 0)

        duplicata_ids = self.condicao_pagamento_id.gera_parcela_ids(valor,
                                                         self.data_emissao)
        valores['duplicata_ids'] = duplicata_ids

        return res

    def _check_permite_alteracao(self, operacao='create', dados={},
                                 campos_proibidos=[]):
        CAMPOS_PERMITIDOS = [
            'message_follower_ids',
            'documento_impresso',
        ]
        for documento in self:
            if documento.permite_alteracao:
                continue

            permite_alteracao = False
            #
            # Trata alguns campos que é permitido alterar depois da nota
            # autorizada
            #
            if documento.situacao_nfe == SITUACAO_NFE_AUTORIZADA:
                for campo in dados:
                    if campo in CAMPOS_PERMITIDOS:
                        permite_alteracao = True
                        break
                    elif campo not in campos_proibidos:
                        campos_proibidos.append(campo)

            if permite_alteracao:
                continue

            if operacao == 'unlink':
                mensagem = \
                    'Não é permitido excluir este documento fiscal!'
            elif operacao == 'write':
                mensagem = \
                    'Não é permitido alterar este documento fiscal!'
            elif operacao == 'create':
                mensagem = \
                    'Não é permitido criar este documento fiscal!'

            if campos_proibidos:
                mensagem += '\nCampos proibidos: '
                mensagem += unicode(campos_proibidos)

            raise ValidationError(_(mensagem))

    def envia_documento(self):
        """ Nunca sobrescreva este método, pois ele esta sendo modificado
        pelo sped_queue que não chama o super. Para permtir o envio assincrono
        do documento fiscal
        :return:
        """
        return self._envia_documento()

    def _envia_documento(self):
        for record in self:
            if not record.numero:
                record.update(record._onchange_serie()['value'])

    def cancela_nfe(self):
        self.ensure_one()
        if any(doc.situacao_nfe == SITUACAO_NFE_AUTORIZADA
               for doc in self.documento_subsequente_ids.mapped(
                'documento_subsequente_id')):
            mensagem = _("Não é permitido cancelar o documento: um ou mais"
                         "documentos associados já foram autorizados.")
            raise UserWarning(mensagem)

    def inutiliza_nfe(self):
        self.ensure_one()

    def executa_antes_autorizar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias antes de autorizar uma NF-e
        #
        self.ensure_one()
        self.gera_operacoes_subsequentes()

    def executa_depois_autorizar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias depois de autorizar uma NF-e,
        # por exemplo, criar lançamentos financeiros, movimentações de
        # estoque etc.
        #
        self.ensure_one()
        self.gera_operacoes_subsequentes()

    def executa_antes_cancelar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias antes de autorizar uma NF-e;
        # não confundir com o método _compute_permite_cancelamento, que indica
        # se o botão de cancelamento vai estar disponível para o usuário na
        # interface
        #
        self.ensure_one()
        self.gera_operacoes_subsequentes()

    def executa_depois_cancelar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias depois de cancelar uma NF-e,
        # por exemplo, excluir lançamentos financeiros, movimentações de
        # estoque etc.
        #
        self.ensure_one()
        self.gera_operacoes_subsequentes()

    def executa_antes_inutilizar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias antes de autorizar uma NF-e
        #
        self.ensure_one()
        self.gera_operacoes_subsequentes()

    def executa_depois_inutilizar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias depois de autorizar uma NF-e,
        # por exemplo, criar lançamentos financeiros, movimentações de
        # estoque etc.
        #
        self.ensure_one()
        self.gera_operacoes_subsequentes()

    def executa_antes_denegar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias antes de denegar uma NF-e
        #
        self.ensure_one()
        self.gera_operacoes_subsequentes()

    def executa_depois_denegar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias depois de denegar uma NF-e,
        # por exemplo, invalidar pedidos de venda e movimentações de estoque
        # etc.
        #
        self.ensure_one()
        self.gera_operacoes_subsequentes()

    def envia_email(self, mail_template):
        self.ensure_one()

    def gera_pdf(self):
        self.write({'documento_impresso': True})

    @api.multi
    def imprimir_documento(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        return self.env['report'].get_action(self, 'report_sped_documento')

    def executa_antes_create(self, dados):
        return dados

    def executa_depois_create(self, result, dados):
        return result

    @api.model
    def create(self, dados):
        dados = self.executa_antes_create(dados)
        result = super(SpedDocumento, self).create(dados)
        return self.executa_depois_create(result, dados)

    def executa_antes_write(self, dados):
        self._check_permite_alteracao(operacao='write', dados=dados)
        return dados

    def write(self, dados):
        self.executa_antes_write(dados)
        result = super(SpedDocumento, self).write(dados)
        return self.executa_depois_write(result, dados)

    def executa_depois_write(self, result, dados):
        return result

    def executa_antes_unlink(self):
        self._check_permite_alteracao(operacao='unlink')

    def unlink(self):
        self.executa_antes_unlink()
        res = super(SpedDocumento, self).unlink()
        return self.executa_depois_unlink(res)

    def executa_depois_unlink(self, result):
        return result

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None,
                    order=None):
        if order is None or not order:
            if self.env.context.get('default_order', False):
                order = self.env.context.get('default_order', False)
            elif self.env.context.get('order', False):
                order = self.env.context.get('order', False)

        return super(SpedDocumento, self).search_read(domain=domain,
            fields=fields, offset=offset, limit=limit, order=order)

    def _prepare_subsequente_referenciado(self):
        vals = {
                'documento_id': self.id,
                'participante_id': self.participante_id.id,
                'modelo': self.modelo,
                'serie': self.serie,
                'numero': self.numero,
                'data_emissao': self.data_emissao,
                'chave': self.chave,
                # 'numero_ecf': self.ecf,
                # 'numero_coo': self.coo,
            }
        refenciado_id = self.env['sped.documento.referenciado'].create(vals)
        return refenciado_id

    def _referencia_documento(self, referencia_ids):
        for referenciado_item in referencia_ids:
            referenciado_item.documento_referenciado_id = self.id
            self.documento_referenciado_ids |= referenciado_item


    @api.multi
    def gera_operacoes_subsequentes(self):
        self._gera_operacoes_subsequentes()

    @api.multi
    def _gera_operacoes_subsequentes(self):
        """
        Operaçoes subsequentes:

            - NOTA FISCAL emitida em operaçao triangular;
                - Simples faturamento 5922;
                - Encomenda de entrega futura: 5117

            - NOTA FISCAL MULTI EMPRESAS ;
                - Saida;
                - Entrada;

            - Consiguinaçao:
                - Remessa de consiguinaçao;
                - Venda de itens;
                - Retorno de consiguinaçao;

            - Venda ambulante:
                - Remessa fora de estabelecimento;
                - Itens vendidos fora do estabelecimento;
                - Retorno de venda fora do estabelecimento;


            Caso o tipo da nota seja diferente devemos inverter os participantes;


        :return:
        """
        for record in self.filtered(lambda doc:
                                    not doc.documentos_subsequentes_gerados):
            for subsequente_id in record.documento_subsequente_ids.filtered(
                    lambda doc_sub: doc_sub._confirma_geracao_documento()):
                subsequente_id.gera_documento_subsequente()
                #
                # Transmite o documento
                #

                # documento.envia_documento()

        # TODO: Retornar usuário para os documentos criados
    
    @api.depends('operacao_id')
    def _compute_documento_subsequente_ids(self):
        for documento in self:
            documento.documento_subsequente_ids = \
                self.env['sped.documento.subsequente'].search([
                    ('documento_origem_id', '=', self.id)
                ])
            if not self.operacao_id:
                continue
            if documento.operacao_id.mapped('operacao_subsequente_ids') == \
                    documento.documento_subsequente_ids.mapped(
                        'operacao_subsequente_id'):
                continue
            self.env['sped.documento.subsequente'].search([
                ('documento_origem_id', '=', documento.id)
            ]).unlink()
            for subsequente_id in documento.operacao_subsequente_ids:
                self.env['sped.documento.subsequente'].create({
                    'documento_origem_id': documento.id,
                    'operacao_subsequente_id': subsequente_id.id,
                    'sped_operacao_id':
                        subsequente_id.operacao_subsequente_id.id,
                })
                documento.documento_subsequente_ids = \
                    self.env['sped.documento.subsequente'].search([
                        ('documento_origem_id', '=', self.id)
                    ])

    @api.depends('documento_subsequente_ids.documento_subsequente_id')
    def _compute_documentos_subsequentes_gerados(self):
        for documento in self:
            if not documento.documento_subsequente_ids:
                continue
            documento.documentos_subsequentes_gerados = all(
                subsequente_id.operacao_realizada
                for subsequente_id in documento.documento_subsequente_ids
            )
