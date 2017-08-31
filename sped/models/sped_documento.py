# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from odoo.addons.l10n_br_base.constante_tributaria import (
    TIPO_EMISSAO_NFE,
    TIPO_EMISSAO,
    MODELO_FISCAL,
    ENTRADA_SAIDA,
    ENTRADA_SAIDA_SAIDA,
    SITUACAO_FISCAL,
    SITUACAO_FISCAL_REGULAR,
    AMBIENTE_NFE,
    AMBIENTE_NFE_HOMOLOGACAO,
    SITUACAO_NFE_AUTORIZADA,
    TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL,
    INDICADOR_IE_DESTINATARIO,
    TIPO_CONSUMIDOR_FINAL_NORMAL,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFSE,
    TIPO_EMISSAO_PROPRIA,
    AMBIENTE_NFE_PRODUCAO,
    TIPO_EMISSAO_NFE_NORMAL,
    ENTRADA_SAIDA_ENTRADA,
    ENTRADA_SAIDA_DICT,
    TIPO_EMISSAO_DICT,
    IE_DESTINATARIO,
    ST_ISS,
    NATUREZA_TRIBUTACAO_NFSE,
    LIMITE_RETENCAO_PIS_COFINS_CSLL,
    MODALIDADE_FRETE_DESTINATARIO_PROPRIO,
    MODALIDADE_FRETE,
    INDICADOR_PRESENCA_COMPRADOR_NAO_SE_APLICA,
    INDICADOR_PRESENCA_COMPRADOR,
    TIPO_CONSUMIDOR_FINAL,
    FINALIDADE_NFE_NORMAL,
    FINALIDADE_NFE,
    IND_FORMA_PAGAMENTO,
    IND_FORMA_PAGAMENTO_A_VISTA,
    REGIME_TRIBUTARIO,
    REGIME_TRIBUTARIO_SIMPLES,
    INDICADOR_IE_DESTINATARIO_CONTRIBUINTE,
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.data import parse_datetime, data_hora_horario_brasilia, \
        formata_data
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.valor import formata_valor

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumento(SpedBase, models.Model):
    _name = b'sped.documento'
    _description = 'Documentos Fiscais'
    _inherit = ['mail.thread']
    _order = 'emissao, modelo, data_emissao desc, serie, numero desc'
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
    )
    hora_emissao = fields.Char(
        string='Hora de emissão',
        size=8,
        compute='_compute_data_hora_separadas',
        store=True,
    )
    data_entrada_saida = fields.Date(
        string='Data de entrada/saída',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )
    hora_entrada_saida = fields.Char(
        string='Hora de entrada/saída',
        size=8,
        compute='_compute_data_hora_separadas',
        store=True,
    )
    serie = fields.Char(
        string='Série',
        size=3,
        index=True,
    )
    numero = fields.Float(
        string='Número',
        index=True,
        digits=(18, 0),
    )
    entrada_saida = fields.Selection(
        selection=ENTRADA_SAIDA,
        string='Entrada/Saída',
        index=True,
        default=ENTRADA_SAIDA_SAIDA,
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
    #
    # Campos da operação
    #
    regime_tributario = fields.Selection(
        selection=REGIME_TRIBUTARIO,
        string='Regime tributário',
        default=REGIME_TRIBUTARIO_SIMPLES,
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
        default=MODALIDADE_FRETE_DESTINATARIO_PROPRIO,
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
    # Transporte
    #
    transportadora_id = fields.Many2one(
        comodel_name='res.partner',
        string='Transportadora',
        ondelete='restrict',
        domain=[['cnpj_cpf', '!=', False]],
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

    item_ids = fields.One2many(
        comodel_name='sped.documento.item',
        inverse_name='documento_id',
        string='Itens',
        copy=True,
    )
    documento_referenciado_ids = fields.One2many(
        comodel_name='sped.documento.referenciado',
        inverse_name='documento_id',
        string='Documentos Referenciados',
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

    @api.depends('modelo', 'emissao')
    def _compute_permite_alteracao(self):
        for documento in self:
            documento.permite_alteracao = True

    @api.depends('modelo', 'emissao')
    def _compute_permite_cancelamento(self):
        for documento in self:
            documento.permite_cancelamento = True

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

    @api.depends(
        'item_ids.vr_nf',
        'item_ids.vr_fatura',
    )
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

            if self.empresa_id.tipo_emissao_nfe == TIPO_EMISSAO_NFE_NORMAL:
                if self.empresa_id.ambiente_nfe == AMBIENTE_NFE_PRODUCAO:
                    valores['serie'] = self.empresa_id.serie_nfe_producao
                else:
                    valores['serie'] = self.empresa_id.serie_nfe_homologacao

            else:
                if self.empresa_id.ambiente_nfe == AMBIENTE_NFE_PRODUCAO:
                    valores['serie'] = (
                        self.empresa_id.serie_nfe_contingencia_producao
                    )
                else:
                    valores['serie'] = (
                        self.empresa_id.serie_nfe_contingencia_homologacao
                    )

        elif self.modelo == MODELO_FISCAL_NFCE:
            valores['ambiente_nfe'] = self.empresa_id.ambiente_nfce
            valores['tipo_emissao_nfe'] = self.empresa_id.tipo_emissao_nfce

            if self.empresa_id.tipo_emissao_nfce == TIPO_EMISSAO_NFE_NORMAL:
                if self.empresa_id.ambiente_nfce == AMBIENTE_NFE_PRODUCAO:
                    valores['serie'] = self.empresa_id.serie_nfce_producao
                else:
                    valores['serie'] = self.empresa_id.serie_nfce_homologacao

            else:
                if self.empresa_id.ambiente_nfce == AMBIENTE_NFE_PRODUCAO:
                    valores['serie'] = (
                        self.empresa_id.serie_nfce_contingencia_producao
                    )
                else:
                    valores['serie'] = (
                        self.empresa_id.serie_nfce_contingencia_homologacao
                    )

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
                valores['natureza_operacao_id'] = (
                    self.operacao_id.natureza_operacao_id.id
                )

            if self.operacao_id.serie:
                valores['serie'] = self.operacao_id.serie

            valores['regime_tributario'] = self.operacao_id.regime_tributario
            valores['ind_forma_pagamento'] = \
                self.operacao_id.ind_forma_pagamento
            if self.operacao_id.condicao_pagamento_id:
                valores['condicao_pagamento_id'] = \
                    self.operacao_id.condicao_pagamento_id.id
            valores['finalidade_nfe'] = self.operacao_id.finalidade_nfe
            valores['modalidade_frete'] = self.operacao_id.modalidade_frete
            valores['infadfisco'] = self.operacao_id.infadfisco
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

        ultimo_numero = self.search([
            ('empresa_id.cnpj_cpf', '=', self.empresa_id.cnpj_cpf),
            ('ambiente_nfe', '=', self.ambiente_nfe),
            ('emissao', '=', self.emissao),
            ('modelo', '=', self.modelo),
            ('serie', '=', self.serie.strip()),
            ('numero', '!=', False),
        ], limit=1, order='numero desc')

        valores['serie'] = self.serie.strip()

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

        #
        # Para a compatibilidade com a chamada original (super), que usa
        # o decorator deprecado api.one, pegamos aqui sempre o 1º elemento
        # da lista que vai ser retornada
        #
        lista_vencimentos = self.condicao_pagamento_id.compute(valor,
                                                         self.data_emissao)[0]

        duplicata_ids = [
            [5, False, {}],
        ]

        parcela = 1
        for data_vencimento, valor in lista_vencimentos:
            duplicata = {
                'numero': str(parcela),
                'data_vencimento': data_vencimento,
                'valor': valor,
            }
            duplicata_ids.append([0, False, duplicata])
            parcela += 1

        valores['duplicata_ids'] = duplicata_ids

        return res

    def _check_permite_alteracao(self, operacao='create', dados={}):
        CAMPOS_PERMITIDOS = [
            'message_follower_ids',
        ]
        for documento in self:
            if documento.permite_alteracao:
                continue

            permite_alteracao = False
            #
            # Trata alguns campos que é permitido alterar depois da nota
            # autorizada
            #
            if documento.state_nfe == SITUACAO_NFE_AUTORIZADA:
                for campo in CAMPOS_PERMITIDOS:
                    if campo in dados:
                        permite_alteracao = True
                        break

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

            raise ValidationError(_(mensagem))

    def unlink(self):
        self._check_permite_alteracao(operacao='unlink')
        return super(SpedDocumento, self).unlink()

    def write(self, dados):
        self._check_permite_alteracao(operacao='write', dados=dados)
        return super(SpedDocumento, self).write(dados)

    def envia_nfe(self):
        pass

    def cancela_nfe(self):
        pass

    def executa_antes_autorizar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias antes de autorizar uma NF-e
        #
        pass

    def executa_depois_autorizar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias depois de autorizar uma NF-e,
        # por exemplo, criar lançamentos financeiros, movimentações de
        # estoque etc.
        #
        pass

    def executa_antes_cancelar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias antes de autorizar uma NF-e;
        # não confundir com o método _compute_permite_cancelamento, que indica
        # se o botão de cancelamento vai estar disponível para o usuário na
        # interface
        #
        pass

    def executa_depois_cancelar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias depois de cancelar uma NF-e,
        # por exemplo, excluir lançamentos financeiros, movimentações de
        # estoque etc.
        #
        pass

    def executa_antes_denegar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias antes de denegar uma NF-e
        #
        pass

    def executa_depois_denegar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias depois de denegar uma NF-e,
        # por exemplo, invalidar pedidos de venda e movimentações de estoque
        # etc.
        #
        pass

    def envia_email(self, mail_template):
        pass

    def gera_pdf(self):
        pass
