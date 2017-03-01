# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from ..constante_tributaria import *
import logging
_logger = logging.getLogger(__name__)

try:
    from pybrasil.data import parse_datetime, data_hora_horario_brasilia, \
        formata_data
    from pybrasil.valor.decimal import Decimal
    from pybrasil.valor import formata_valor

except (ImportError, IOError) as err:
    _logger.debug(err)


class Documento(models.Model):
    _description = u'Documento Fiscal'
    _inherit = ['sped.base', 'mail.thread']
    _name = 'sped.documento'
    _order = 'emissao, modelo, data_emissao desc, serie, numero desc'
    _rec_name = 'descricao'

    descricao = fields.Char(
        string=u'Documento Fiscal',
        compute='_compute_descricao',
    )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string=u'Empresa',
        ondelete='restrict',
        default=lambda self:
        self.env['sped.empresa']._empresa_ativa('sped.documento')
    )
    empresa_cnpj_cpf = fields.Char(
        string=u'CNPJ/CPF',
        size=18,
        related='empresa_id.cnpj_cpf',
        readonly=True,
    )
    emissao = fields.Selection(
        selection=TIPO_EMISSAO,
        string=u'Tipo de emissão',
        index=True,
    )
    modelo = fields.Selection(
        selection=MODELO_FISCAL,
        string=u'Modelo',
        index=True,
    )
    data_hora_emissao = fields.Datetime(
        string=u'Data de emissão',
        index=True,
        default=fields.Datetime.now,
    )
    data_hora_entrada_saida = fields.Datetime(
        string=u'Data de entrada/saída',
        index=True,
        default=fields.Datetime.now,
    )
    data_emissao = fields.Date(
        string=u'Data de emissão',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )
    hora_emissao = fields.Char(
        'Hora de emissão',
        size=8,
        compute='_compute_data_hora_separadas',
        store=True,
    )
    data_entrada_saida = fields.Date(
        string=u'Data de entrada/saída',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )
    hora_entrada_saida = fields.Char(
        string=u'Hora de entrada/saída',
        size=8,
        compute='_compute_data_hora_separadas',
        store=True,
    )
    serie = fields.Char(
        string=u'Série',
        size=3,
        index=True,
    )
    numero = fields.Float(
        string=u'Número',
        index=True,
        digits=(18, 0),
    )
    entrada_saida = fields.Selection(
        selection=ENTRADA_SAIDA,
        string=u'Entrada/Saída',
        index=True,
        default=ENTRADA_SAIDA_SAIDA,
    )
    situacao_fiscal = fields.Selection(
        selection=SITUACAO_FISCAL,
        string=u'Situação fiscal',
        index=True,
        default=SITUACAO_FISCAL_REGULAR,
    )
    ambiente_nfe = fields.Selection(
        selection=AMBIENTE_NFE,
        string=u'Ambiente da NF-e',
        index=True,
        default=AMBIENTE_NFE_HOMOLOGACAO,
    )
    tipo_emissao_nfe = fields.Selection(
        selection=TIPO_EMISSAO_NFE,
        string=u'Tipo de emissão da NF-e',
        default=TIPO_EMISSAO_NFE_NORMAL,
    )
    ie_st = fields.Char(
        string=u'IE do substituto tributário',
        size=14,
    )
    municipio_fato_gerador_id = fields.Many2one(
        comodel_name='sped.municipio',
        string=u'Município do fato gerador',
    )
    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        string=u'Operação',
        ondelete='restrict',
    )
    #
    # Campos da operação
    #
    regime_tributario = fields.Selection(
        selection=REGIME_TRIBUTARIO,
        string=u'Regime tributário',
        default=REGIME_TRIBUTARIO_SIMPLES,
    )
    ind_forma_pagamento = fields.Selection(
        selection=IND_FORMA_PAGAMENTO,
        string=u'Tipo de pagamento',
        default=IND_FORMA_PAGAMENTO_A_VISTA,
    )
    finalidade_nfe = fields.Selection(
        selection=FINALIDADE_NFE,
        string=u'Finalidade da NF-e',
        default=FINALIDADE_NFE_NORMAL,
    )
    consumidor_final = fields.Selection(
        selection=TIPO_CONSUMIDOR_FINAL,
        string=u'Tipo do consumidor',
        default=TIPO_CONSUMIDOR_FINAL_NORMAL,
    )
    presenca_comprador = fields.Selection(
        selection=INDICADOR_PRESENCA_COMPRADOR,
        string=u'Presença do comprador',
        default=INDICADOR_PRESENCA_COMPRADOR_NAO_SE_APLICA,
    )
    modalidade_frete = fields.Selection(
        selection=MODALIDADE_FRETE,
        string=u'Modalidade do frete',
        default=MODALIDADE_FRETE_DESTINATARIO_PROPRIO,
    )
    natureza_operacao_id = fields.Many2one(
        comodel_name='sped.natureza.operacao',
        string=u'Natureza da operação',
        ondelete='restrict',
    )
    infadfisco = fields.Text(
        string=u'Informações adicionais de interesse do fisco'
    )
    infcomplementar = fields.Text(
        string=u'Informações complementares'
    )
    deduz_retencao = fields.Boolean(
        string=u'Deduz retenção do total da NF?',
        default=True
    )
    pis_cofins_retido = fields.Boolean(
        string=u'PIS-COFINS retidos?'
    )
    al_pis_retido = fields.Monetary(
        string=u'Alíquota do PIS',
        default=0.65,
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_cofins_retido = fields.Monetary(
        string=u'Alíquota da COFINS',
        default=3,
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    csll_retido = fields.Boolean(
        string=u'CSLL retido?',
    )
    al_csll = fields.Monetary(
        string=u'Alíquota da CSLL',
        default=1,
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    limite_retencao_pis_cofins_csll = fields.Monetary(
        string=u'Obedecer limite de faturamento para retenção de',
        default=LIMITE_RETENCAO_PIS_COFINS_CSLL,
    )
    irrf_retido = fields.Boolean(
        string=u'IR retido?',
    )
    irrf_retido_ignora_limite = fields.Boolean(
        string=u'IR retido ignora limite de R$ 10,00?',
    )
    al_irrf = fields.Monetary(
        string=u'Alíquota do IR',
        default=1,
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    inss_retido = fields.Boolean(
        string=u'INSS retido?',
        index=True,
    )
    al_inss_retido = fields.Monetary(
        string=u'Alíquota do INSS',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_inss = fields.Monetary(
        u'Alíquota do INSS',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    cnae_id = fields.Many2one(
        comodel_name='sped.cnae',
        string=u'CNAE',
    )
    natureza_tributacao_nfse = fields.Selection(
        selection=NATUREZA_TRIBUTACAO_NFSE,
        string=u'Natureza da tributação',
    )
    servico_id = fields.Many2one(
        comodel_name='sped.servico',
        string=u'Serviço',
    )
    cst_iss = fields.Selection(
        selection=ST_ISS,
        string=u'CST ISS',
    )
    #
    # Destinatário/Remetente
    #
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string=u'Destinatário/Remetente',
        ondelete='restrict',
    )
    participante_cnpj_cpf = fields.Char(
        string=u'CNPJ/CPF',
        size=18,
        related='participante_id.cnpj_cpf',
        readonly=True,
    )
    participante_tipo_pessoa = fields.Char(
        string=u'Tipo pessoa',
        size=1,
        related='participante_id.tipo_pessoa',
        readonly=True,
    )
    participante_razao_social = fields.Char(
        string=u'Razão Social',
        size=60,
        related='participante_id.razao_social',
        readonly=True,
    )
    participante_fantasia = fields.Char(
        string=u'Fantasia',
        size=60,
        related='participante_id.fantasia',
        readonly=True,
    )
    participante_endereco = fields.Char(
        string=u'Endereço',
        size=60,
        related='participante_id.endereco',
        readonly=True,
    )
    participante_numero = fields.Char(
        string=u'Número',
        size=60,
        related='participante_id.numero',
        readonly=True,
    )
    participante_complemento = fields.Char(
        string=u'Complemento',
        size=60,
        related='participante_id.complemento',
        readonly=True,
    )
    participante_bairro = fields.Char(
        string=u'Bairro',
        size=60,
        related='participante_id.bairro',
        readonly=True,
    )
    participante_municipio_id = fields.Many2one(
        comodel_name='sped.municipio',
        string=u'Município',
        related='participante_id.municipio_id',
        readonly=True,
    )
    participante_cidade = fields.Char(
        string=u'Município',
        related='participante_id.cidade',
        readonly=True,
    )
    participante_estado = fields.Char(
        string=u'Estado',
        related='participante_id.estado',
        readonly=True,
    )
    participante_cep = fields.Char(
        string=u'CEP',
        size=9,
        related='participante_id.cep',
        readonly=True,
    )
    #
    # Telefone e email para a emissão da NF-e
    #
    participante_fone = fields.Char(
        string=u'Fone',
        size=18,
        related='participante_id.fone',
        readonly=True,
    )
    participante_fone_comercial = fields.Char(
        string=u'Fone Comercial',
        size=18,
        related='participante_id.fone_comercial',
        readonly=True,
    )
    participante_celular = fields.Char(
        string=u'Celular',
        size=18,
        related='participante_id.celular',
        readonly=True,
    )
    participante_email = fields.Char(
        string=u'Email',
        size=60,
        related='participante_id.email',
        readonly=True,
    )
    #
    # Inscrições e documentos
    #
    participante_contribuinte = fields.Selection(
        selection=IE_DESTINATARIO,
        string=u'Contribuinte',
        default='2',
        related='participante_id.contribuinte',
        readonly=True,
    )
    participante_ie = fields.Char(
        string=u'Inscrição estadual',
        size=18,
        related='participante_id.ie',
        readonly=True,
    )
    participante_eh_orgao_publico = fields.Boolean(
        string=u'É órgão público?',
        related='participante_id.eh_orgao_publico',
        readonly=True,
    )

    #
    # Chave e validação da chave
    #
    chave = fields.Char(
        string=u'Chave',
        size=44,
    )
    #
    # Duplicatas e pagamentos
    #
    payment_term_id = fields.Many2one(
        comodel_name='account.payment.term',
        string=u'Forma de pagamento',
        ondelete='restrict',
    )
    duplicata_ids = fields.One2many(
        comodel_name='sped.documento.duplicata',
        inverse_name='documento_id',
        string=u'Duplicatas',
    )
    pagamento_ids = fields.One2many(
        comodel_name='sped.documento.pagamento',
        inverse_name='documento_id',
        string=u'Pagamentos',
    )

    #
    # Transporte
    #
    transportadora_id = fields.Many2one(
        comodel_name='res.partner',
        string=u'Transportadora',
        ondelete='restrict',
        domain=[
            ('cnpj_cpf', '!=', False)  # TODO: eh_transportadora do participant
        ],
    )
    veiculo_id = fields.Many2one(
        comodel_name='sped.veiculo',
        string=u'Veículo',
        ondelete='restrict',
    )
    reboque_1_id = fields.Many2one(
        comodel_name='sped.veiculo',
        string=u'Reboque 1',
        ondelete='restrict',
    )
    reboque_2_id = fields.Many2one(
        comodel_name='sped.veiculo',
        string=u'Reboque 2',
        ondelete='restrict',
    )
    reboque_3_id = fields.Many2one(
        comodel_name='sped.veiculo',
        string=u'Reboque 3',
        ondelete='restrict',
    )
    reboque_4_id = fields.Many2one(
        comodel_name='sped.veiculo',
        string=u'Reboque 4',
        ondelete='restrict',
    )
    reboque_5_id = fields.Many2one(
        comodel_name='sped.veiculo',
        string=u'Reboque 5',
        ondelete='restrict',
    )

    volume_ids = fields.One2many(
        comodel_name='sped.documento.volume',
        inverse_name='documento_id',
        string=u'Volumes'
    )

    #
    # Exportação
    #
    exportacao_estado_embarque_id = fields.Many2one(
        comodel_name='sped.estado',
        string=u'Estado do embarque',
        ondelete='restrict',
    )
    exportacao_local_embarque = fields.Char(
        string=u'Local do embarque',
        size=60,
    )

    #
    # Compras públicas
    #
    compra_nota_empenho = fields.Char(
        string=u'Identificação da nota de empenho (compra pública)',
        size=17,
    )
    compra_pedido = fields.Char(
        string=u'Pedido (compra pública)',
        size=60,
    )
    compra_contrato = fields.Char(
        string=u'Contrato (compra pública)',
        size=60,
    )
    #
    # Totais dos itens
    #

    # Valor total dos produtos
    vr_produtos = fields.Monetary(
        string=u'Valor dos produtos/serviços',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_produtos_tributacao = fields.Monetary(
        string=u'Valor dos produtos para tributação',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_frete = fields.Monetary(
        string=u'Valor do frete',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_seguro = fields.Monetary(
        string=u'Valor do seguro',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_desconto = fields.Monetary(
        string=u'Valor do desconto',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_outras = fields.Monetary(
        string=u'Outras despesas acessórias',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_operacao = fields.Monetary(
        string=u'Valor da operação',
        compute='_compute_soma_itens',
        store=True
    )
    vr_operacao_tributacao = fields.Monetary(
        string=u'Valor da operação para tributação',
        compute='_compute_soma_itens',
        store=True
    )
    # ICMS próprio
    bc_icms_proprio = fields.Monetary(
        string=u'Base do ICMS próprio',
        compute='_compute_soma_itens',
        store=True
    )
    vr_icms_proprio = fields.Monetary(
        string=u'Valor do ICMS próprio',
        compute='_compute_soma_itens',
        store=True
    )
    # ICMS SIMPLES
    vr_icms_sn = fields.Monetary(
        string=u'Valor do crédito de ICMS - SIMPLES Nacional',
        compute='_compute_soma_itens',
        store=True
    )
    vr_simples = fields.Monetary(
        string=u'Valor do SIMPLES Nacional',
        compute='_compute_soma_itens',
        store=True,
    )
    # ICMS ST
    bc_icms_st = fields.Monetary(
        string=u'Base do ICMS ST',
        compute='_compute_soma_itens',
        store=True
    )
    vr_icms_st = fields.Monetary(
        string=u'Valor do ICMS ST',
        compute='_compute_soma_itens',
        store=True,
    )
    # ICMS ST retido
    bc_icms_st_retido = fields.Monetary(
        string=u'Base do ICMS retido anteriormente por '
               u'substituição tributária',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_icms_st_retido = fields.Monetary(
        string=u'Valor do ICMS retido anteriormente por '
               u'substituição tributária',
        compute='_compute_soma_itens',
        store=True,
    )
    # IPI
    bc_ipi = fields.Monetary(
        string=u'Base do IPI',
        compute='_compute_soma_itens',
        store=True
    )
    vr_ipi = fields.Monetary(
        string=u'Valor do IPI',
        compute='_compute_soma_itens',
        store=True,
    )
    # Imposto de importação
    bc_ii = fields.Monetary(
        string=u'Base do imposto de importação',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_despesas_aduaneiras = fields.Monetary(
        string=u'Despesas aduaneiras',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_ii = fields.Monetary(
        string=u'Valor do imposto de importação',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_iof = fields.Monetary(
        string=u'Valor do IOF',
        compute='_compute_soma_itens',
        store=True,
    )
    # PIS e COFINS
    bc_pis_proprio = fields.Monetary(
        string=u'Base do PIS próprio',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_pis_proprio = fields.Monetary(
        string=u'Valor do PIS próprio',
        compute='_compute_soma_itens',
        store=True,
    )
    bc_cofins_proprio = fields.Monetary(
        string=u'Base da COFINS própria',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_cofins_proprio = fields.Monetary(
        string=u'Valor do COFINS própria',
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
        string=u'Base do ISS',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_iss = fields.Monetary(
        string=u'Valor do ISS',
        compute='_compute_soma_itens',
        store=True,
    )
    # Total da NF e da fatura (podem ser diferentes no caso de operação
    # triangular)
    vr_nf = fields.Monetary(
        string=u'Valor da NF',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_fatura = fields.Monetary(
        string=u'Valor da fatura',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_ibpt = fields.Monetary(
        string=u'Valor IBPT',
        compute='_compute_soma_itens',
        store=True,
    )
    bc_inss_retido = fields.Monetary(
        string=u'Base do INSS',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_inss_retido = fields.Monetary(
        string=u'Valor do INSS',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_custo_comercial = fields.Monetary(
        string=u'Custo comercial',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_difal = fields.Monetary(
        string=u'Valor do diferencial de alíquota ICMS próprio',
        compute='_compute_soma_itens',
        store=True,
    )
    vr_fcp = fields.Monetary(
        string=u'Valor do fundo de combate à pobreza',
        compute='_compute_soma_itens',
        store=True,
    )
    ###
    # Retenções de tributos (órgãos públicos, substitutos tributários etc.)
    ###
    # 'vr_operacao_pis_cofins_csll = CampoDinheiro(
    # u'Base da retenção do PIS-COFINS e CSLL'),

    # PIS e COFINS
    # 'pis_cofins_retido = fields.boolean(u'PIS-COFINS retidos?'),
    # 'al_pis_retido = CampoPorcentagem(u'Alíquota do PIS retido'),
    # 'vr_pis_retido = CampoDinheiro(u'PIS retido'),
    # 'al_cofins_retido = CampoPorcentagem(u'Alíquota da COFINS retida'),
    # 'vr_cofins_retido = CampoDinheiro(u'COFINS retida'),

    # Contribuição social sobre lucro líquido
    # 'csll_retido = fields.boolean(u'CSLL retida?'),
    # 'al_csll = CampoPorcentagem('Alíquota da CSLL'),
    # 'vr_csll = CampoDinheiro(u'CSLL retida'),
    # 'bc_csll_propria = CampoDinheiro(u'Base da CSLL própria'),
    # 'al_csll_propria = CampoPorcentagem('Alíquota da CSLL própria'),
    # 'vr_csll_propria = CampoDinheiro(u'CSLL própria'),

    # IRRF
    # 'irrf_retido = fields.boolean(u'IR retido?'),
    # 'bc_irrf = CampoDinheiro(u'Base do IRRF'),
    # 'al_irrf = CampoPorcentagem(u'Alíquota do IRRF'),
    # 'vr_irrf = CampoDinheiro(u'Valor do IRRF'),
    # 'bc_irpj_proprio = CampoDinheiro(u'Valor do IRPJ próprio'),
    # 'al_irpj_proprio = CampoPorcentagem(u'Alíquota do IRPJ próprio'),
    # 'vr_irpj_proprio = CampoDinheiro(u'Valor do IRPJ próprio'),

    # ISS
    # 'iss_retido = fields.boolean(u'ISS retido?'),
    # 'bc_iss_retido = CampoDinheiro(u'Base do ISS'),
    # 'vr_iss_retido = CampoDinheiro(u'Valor do ISS'),

    item_ids = fields.One2many(
        comodel_name='sped.documento.item',
        inverse_name='documento_id',
        string=u'Itens',
    )
    documento_referenciado_ids = fields.One2many(
        comodel_name='sped.documento.referenciado',
        inverse_name='documento_id',
        string=u'Documentos Referenciados',
    )
    #
    # Outras informações
    #
    eh_compra = fields.Boolean(
        string=u'É compra?',
        compute='_compute_eh_compra_venda',
    )
    eh_venda = fields.Boolean(
        string=u'É venda?',
        compute='_compute_eh_compra_venda',
    )
    eh_devolucao_compra = fields.Boolean(
        string=u'É devolução de compra?',
        compute='_compute_eh_compra_venda',
    )
    eh_devolucao_venda = fields.Boolean(
        string=u'É devolução de venda?',
        compute='_compute_eh_compra_venda',
    )
    permite_alteracao = fields.Boolean(
        string=u'Permite alteração?',
        compute='_compute_permite_alteracao',
    )
    permite_cancelamento = fields.Boolean(
        string=u'Permite cancelamento?',
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
            data_hora_emissao = data_hora_horario_brasilia(
                parse_datetime(documento.data_hora_emissao))
            documento.data_emissao = str(data_hora_emissao)[:10]
            documento.hora_emissao = str(data_hora_emissao)[11:19]

            data_hora_entrada_saida = data_hora_horario_brasilia(
                parse_datetime(documento.data_hora_entrada_saida))
            documento.data_entrada_saida = str(data_hora_entrada_saida)[:10]
            documento.hora_entrada_saida = str(data_hora_entrada_saida)[11:19]

    @api.depends('item_ids')
    def _compute_soma_itens(self):
        CAMPOS_SOMA_ITENS = [
            'vr_produtos', 'vr_produtos_tributacao',
            'vr_frete', 'vr_seguro', 'vr_desconto', 'vr_outras',
            'vr_operacao', 'vr_operacao_tributacao',
            'bc_icms_proprio', 'vr_icms_proprio',
            'vr_difal', 'vr_fcp',
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
                dados[campo] = Decimal(0)

            for item in documento.item_ids:
                for campo in CAMPOS_SOMA_ITENS:
                    dados[campo] += getattr(item, campo, Decimal(0))

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
    def onchange_empresa_id(self):
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
    def onchange_operacao_id(self):
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
            valores['ind_forma_pagamento'] = self.operacao_id.ind_forma_pagamento
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
    def onchange_serie(self):
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
        ], limit=1, order='numero desc')

        valores['serie'] = self.serie.strip()

        if len(ultimo_numero) == 0:
            valores['numero'] = 1
        else:
            valores['numero'] = ultimo_numero[0].numero + 1

        return res

    @api.depends('consumidor_final')
    @api.onchange('participante_id')
    def onchange_participante_id(self):
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
                if (self.participante_id.contribuinte !=
                        INDICADOR_IE_DESTINATARIO):
                    valores['consumidor_final'] = (
                        TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL
                    )
        return res

    @api.onchange('payment_term_id', 'vr_fatura', 'vr_nf', 'data_emissao', 'duplicata_ids')
    def _onchange_payment_term(self):
        res = {}
        valores = {}
        res['value'] = valores

        if not (self.payment_term_id and (self.vr_fatura or self.vr_nf) and
                self.data_emissao):
            return res

        valor = Decimal(self.vr_fatura or 0)
        if not valor:
            valor = Decimal(self.vr_nf or 0)

        lista_vencimentos = self.payment_term_id.compute(valor,
                                                         self.data_emissao)

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
                    u'Não é permitido excluir este documento fiscal!'
            elif operacao == 'write':
                mensagem = \
                    u'Não é permitido alterar este documento fiscal!'
            elif operacao == 'create':
                mensagem = \
                    u'Não é permitido criar este documento fiscal!'

            raise ValidationError(mensagem)

    def unlink(self):
        self._check_permite_alteracao(operacao='unlink')
        return super(Documento, self).unlink()

    def write(self, dados):
        self._check_permite_alteracao(operacao='write', dados=dados)
        return super(Documento, self).write(dados)
