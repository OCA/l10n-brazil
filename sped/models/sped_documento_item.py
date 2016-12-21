# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

import logging
_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from ..constante_tributaria import *


class DocumentoItem(models.Model):
    _description = 'Item do Documento Fiscal'
    _name = 'sped.documento.item'
    # _order = 'emissao, modelo, data_emissao desc, serie, numero'
    # _rec_name = 'numero'

    documento_id = fields.Many2one('sped.documento', 'Documento', ondelete='cascade', required=True)
    regime_tributario = fields.Selection(REGIME_TRIBUTARIO, 'Regime tributário',
                                         related='documento_id.regime_tributario', readonly=True)
    modelo = fields.Selection(MODELO_FISCAL, 'Modelo', related='documento_id.modelo', readonly=True)
    empresa_id = fields.Many2one('sped.empresa', 'Empresa', related='documento_id.empresa_id', readonly=True)
    participante_id = fields.Many2one('sped.participante', 'Destinatário/Remetente',
                                      related='documento_id.participante_id', readonly=True)
    operacao_id = fields.Many2one('sped.operacao', 'Operação Fiscal', related='documento_id.operacao_id', readonly=True)
    contribuinte = fields.Selection(IE_DESTINATARIO, string='Contribuinte', related='participante_id.contribuinte',
                                    readonly=True)
    emissao = fields.Selection(TIPO_EMISSAO, 'Tipo de emissão', related='documento_id.emissao', readonly=True)
    data_emissao = fields.Date('Data de emissão', related='documento_id.data_emissao', readonly=True)
    entrada_saida = fields.Selection(ENTRADA_SAIDA, 'Entrada/saída', related='documento_id.entrada_saida',
                                     readonly=True)
    consumidor_final = fields.Selection(TIPO_CONSUMIDOR_FINAL, 'Tipo do consumidor',
                                        related='documento_id.consumidor_final', readonly=True)

    # empresa_id = fields.Many2one('res.empresa', 'Empresa', ondelete='restrict', related='documento_id.empresa_id')
    # emissao = fields.Selection(TIPO_EMISSAO, 'Tipo de emissão', related='documento_id.emissao')
    # modelo = fields.Selection(MODELO_FISCAL, 'Modelo', related='documento_id.modelo')
    # data_hora_emissao = fields.Datetime('Data de emissão', related='documento_id.data_hora_emissao')
    # data_hora_entrada_saida = fields.Datetime('Data de entrada/saída', related='documento_id.data_hora_entrada_saida')
    # data_emissao = fields.Date('Data de emissão', related='documento_id.data_emissao')
    # hora_emissao = fields.Char('Hora de emissão', size=8, related='documento_id.hora_emissao')
    # data_entrada_saida = fields.Date('Data de entrada/saída', related='documento_id.data_entrada_saida')
    # hora_entrada_saida = fields.Char('Hora de entrada/saída', size=8, related='documento_id.hora_entrada_saida')
    ##serie = fields.Char('Série', index=True)
    ##numero = fields.Numero('Número', index=True)
    ##entrada_saida = fields.Selection(ENTRADA_SAIDA, 'Entrada/Saída', index=True, default=ENTRADA_SAIDA_SAIDA)
    ##situacao_fiscal = fields.Selection(SITUACAO_FISCAL, 'Situação fiscal', index=True, default=SITUACAO_FISCAL_REGULAR)

    ##ambiente_nfe =  fields.Selection(AMBIENTE_NFE, 'Ambiente da NF-e', index=True, default=AMBIENTE_NFE_HOMOLOGACAO)
    ##tipo_emissao_nfe = fields.Selection(TIPO_EMISSAO_NFE, 'Tipo de emissão da NF-e', default=TIPO_EMISSAO_NFE_NORMAL)
    ##ie_st = fields.Char('IE do substituto tributário', size=14)
    ##municipio_fato_gerador_id = fields.Many2one('sped.municipio', 'Município do fato gerador')

    ##operacao_id = fields.Many2one('sped.operacao', 'Operação', ondelete='restrict')
    ###
    ### Campos da operação
    ###
    ##regime_tributario = fields.Selection(REGIME_TRIBUTARIO, 'Regime tributário', default=REGIME_TRIBUTARIO_SIMPLES)
    ##forma_pagamento = fields.Selection(FORMA_PAGAMENTO, 'Forma de pagamento', default=FORMA_PAGAMENTO_A_VISTA)
    ##finalidade_nfe = fields.Selection(FINALIDADE_NFE, 'Finalidade da NF-e', default=FINALIDADE_NFE_NORMAL)
    ##modalidade_frete = fields.Selection(MODALIDADE_FRETE, 'Modalidade do frete', default=MODALIDADE_FRETE_DESTINATARIO)
    ##natureza_operacao_id = fields.Many2one('sped.natureza.operacao', 'Natureza da operação', ondelete='restrict')
    ##infadfisco =  fields.Text('Informações adicionais de interesse do fisco')
    ##infcomplementar = fields.Text('Informações complementares')
    ##deduz_retencao = fields.Boolean('Deduz retenção do total da NF?', default=True)
    ##pis_cofins_retido = fields.Boolean('PIS-COFINS retidos?')
    ##al_pis_retido = fields.Porcentagem('Alíquota do PIS', default=0.65)
    ##al_cofins_retido = fields.Porcentagem('Alíquota da COFINS', default=3)
    ##csll_retido = fields.Boolean('CSLL retido?')
    ##al_csll =  fields.Porcentagem('Alíquota da CSLL', default=1)
    ##limite_retencao_pis_cofins_csll = fields.Dinheiro('Obedecer limite de faturamento para retenção de', default=5000)
    ##irrf_retido = fields.Boolean('IR retido?')
    ##irrf_retido_ignora_limite = fields.Boolean('IR retido ignora limite de R$ 10,00?')
    ##al_irrf =  fields.Porcentagem('Alíquota do IR', default=1)
    ##previdencia_retido = fields.Boolean('INSS retido?')
    ##cnae_id = fields.Many2one('sped.cnae', 'CNAE')
    ##natureza_tributacao_nfse = fields.Selection(NATUREZA_TRIBUTACAO_NFSE, 'Natureza da tributação')
    ##servico_id = fields.Many2one('sped.servico', 'Serviço')
    ##cst_iss = fields.Selection(ST_ISS, 'CST ISS')

    cfop_id = fields.Many2one('sped.cfop', 'CFOP', ondelete='restrict', index=True)
    cfop_posicao = fields.Selection(POSICAO_CFOP, 'Posição da CFOP', related='cfop_id.posicao', readonly=True)
    cfop_eh_venda = fields.Boolean('CFOP é venda?', related='cfop_id.eh_venda', readonly=True)
    cfop_eh_devolucao_compra = fields.Boolean('CFOP é devolução de compra?', related='cfop_id.eh_devolucao_compra', readonly=True)
    cfop_eh_retorno_saida = fields.Boolean('CFOP é retorno saída?', related='cfop_id.eh_retorno_saida', readonly=True)
    compoe_total = fields.Boolean('Compõe o valor total da NF-e?', index=True, default=True)
    movimentacao_fisica = fields.Boolean('Há movimentação física do produto?', default=True)

    # Dados do produto/serviço
    produto_id = fields.Many2one('sped.produto', 'Produto/Serviço', ondelete='restrict', index=True)

    protocolo_id = fields.Many2one('sped.protocolo.icms', 'Protocolo ICMS', ondelete='restrict')
    operacao_item_id = fields.Many2one('sped.operacao.item', 'Item da operação fiscal', ondelete='restrict')

    quantidade = fields.Quantidade('Quantidade', default=1)
    unidade_id = fields.Many2one('sped.unidade', 'Unidade', ondelete='restrict')
    vr_unitario = fields.Unitario('Valor unitário')

    # Quantidade de tributação
    fator_conversao_unidade_tributacao = fields.Quantidade('Fator de conversão entre as unidades', default=1)
    quantidade_tributacao = fields.Quantidade('Quantidade para tributação')
    unidade_tributacao_id = fields.Many2one('sped.unidade', 'Unidade para tributação', ondelete='restrict')
    vr_unitario_tributacao = fields.Unitario('Valor unitário para tributação')

    # Valor total dos produtos
    vr_produtos = fields.Dinheiro('Valor do produto/serviço')
    vr_produtos_tributacao = fields.Dinheiro('Valor do produto/serviço para tributação')

    # Outros valores acessórios
    vr_frete = fields.Dinheiro('Valor do frete')
    vr_seguro = fields.Dinheiro('Valor do seguro')
    vr_desconto = fields.Dinheiro('Valor do desconto')
    vr_outras = fields.Dinheiro('Outras despesas acessórias')
    vr_operacao = fields.Dinheiro('Valor da operação')
    vr_operacao_tributacao = fields.Dinheiro('Valor da operação para tributação')

    #
    # ICMS próprio
    #
    # contribuinte = fields.related('participante_id', 'contribuinte', type='char', string=u'Contribuinte', store=False, index=True)
    org_icms = fields.Selection(ORIGEM_MERCADORIA, 'Origem da mercadoria', index=True,
                                default=ORIGEM_MERCADORIA_NACIONAL)
    cst_icms = fields.Selection(ST_ICMS, 'CST ICMS', index=True)
    partilha = fields.Boolean('Partilha de ICMS entre estados (CST 10 ou 90)?')
    al_bc_icms_proprio_partilha = fields.Porcentagem('% da base de cálculo da operação própria')
    estado_partilha_id = fields.Many2one('sped.estado', 'Estado para o qual é devido o ICMS ST', index=True)
    repasse = fields.Boolean('Repasse de ICMS retido anteriosvente entre estados (CST 41)?', index=True)
    md_icms_proprio = fields.Selection(MODALIDADE_BASE_ICMS_PROPRIO, 'Modalidade da base de cálculo do ICMS próprio',
                                       default=MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO)
    pr_icms_proprio = fields.Quantidade('Parâmetro do ICMS próprio')
    rd_icms_proprio = fields.Porcentagem('% de redução da base de cálculo do ICMS próprio')
    bc_icms_proprio_com_ipi = fields.Boolean('IPI integra a base do ICMS próprio?')
    bc_icms_proprio = fields.Dinheiro('Base do ICMS próprio')
    al_icms_proprio = fields.Porcentagem('alíquota do ICMS próprio')
    vr_icms_proprio = fields.Dinheiro('valor do ICMS próprio')

    #
    # Parâmetros relativos ao ICMS Simples Nacional
    #
    cst_icms_sn = fields.Selection(ST_ICMS_SN, 'CST ICMS - SIMPLES', index=True)
    al_icms_sn = fields.Porcentagem('Alíquota do crédito de ICMS')
    rd_icms_sn = fields.Porcentagem('% estadual de redução da alíquota de ICMS')
    vr_icms_sn = fields.Dinheiro('valor do crédito de ICMS - SIMPLES')
    al_simples = fields.Dinheiro('Alíquota do SIMPLES')
    vr_simples = fields.Dinheiro('Valor do SIMPLES')

    #
    # ICMS ST
    #
    md_icms_st = fields.Selection(MODALIDADE_BASE_ICMS_ST, 'Modalidade da base de cálculo do ICMS ST',
                                  default=MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO)
    pr_icms_st = fields.Quantidade('Parâmetro do ICMS ST')
    rd_icms_st = fields.Porcentagem('% de redução da base de cálculo do ICMS ST')
    bc_icms_st_com_ipi = fields.Boolean('IPI integra a base do ICMS ST?')
    bc_icms_st = fields.Dinheiro('Base do ICMS ST')
    al_icms_st = fields.Porcentagem('Alíquota do ICMS ST')
    vr_icms_st = fields.Dinheiro('Valor do ICMS ST')

    #
    # Parâmetros relativos ao ICMS retido anteriormente por substituição tributária
    # na origem
    #
    md_icms_st_retido = fields.Selection(MODALIDADE_BASE_ICMS_ST, 'Modalidade da base de cálculo',
                                         default=MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO)
    pr_icms_st_retido = fields.Quantidade('Parâmetro da base de cáculo')
    rd_icms_st_retido = fields.Porcentagem('% de redução da base de cálculo do ICMS retido')
    bc_icms_st_retido = fields.Dinheiro('Base do ICMS ST retido na origem')
    al_icms_st_retido = fields.Porcentagem('Alíquota do ICMS ST retido na origem')
    vr_icms_st_retido = fields.Dinheiro('Valor do ICMS ST retido na origem')

    #
    # IPI padrão
    #
    apuracao_ipi = fields.Selection(APURACAO_IPI, 'Período de apuração do IPI', index=True, default=APURACAO_IPI_MENSAL)
    cst_ipi = fields.Selection(ST_IPI, 'CST IPI', index=True)
    cst_ipi_entrada = fields.Selection(ST_IPI_ENTRADA, 'CST IPI')
    cst_ipi_saida = fields.Selection(ST_IPI_SAIDA, 'CST IPI')
    md_ipi = fields.Selection(MODALIDADE_BASE_IPI, 'Modalidade BC do IPI', default=MODALIDADE_BASE_IPI_ALIQUOTA)
    bc_ipi = fields.Dinheiro('Base do IPI')
    al_ipi = fields.Quantidade('Alíquota do IPI')
    vr_ipi = fields.Dinheiro('Valor do IPI')

    #
    # Imposto de importação
    #
    bc_ii = fields.Dinheiro('Base do imposto de importação')
    vr_despesas_aduaneiras = fields.Dinheiro('Despesas aduaneiras')
    vr_ii = fields.Dinheiro('Valor do imposto de importação')
    vr_iof = fields.Dinheiro('Valor do IOF')
    numero_fci = fields.Char('Nº controle FCI', size=36)

    #
    # PIS próprio
    #
    al_pis_cofins_id = fields.Many2one('sped.aliquota.pis.cofins', 'Alíquota e CST do PIS-COFINS', index=True)
    cst_pis = fields.Selection(ST_PIS, 'CST PIS', index=True)
    cst_pis_entrada = fields.Selection(ST_PIS_ENTRADA, 'CST PIS')
    cst_pis_saida = fields.Selection(ST_PIS_SAIDA, 'CST PIS')
    md_pis_proprio = fields.Selection(MODALIDADE_BASE_PIS, 'Modalidade BC do PIS próprio',
                                      default=MODALIDADE_BASE_PIS_ALIQUOTA)
    bc_pis_proprio = fields.Dinheiro('Base do PIS próprio')
    al_pis_proprio = fields.Quantidade('Alíquota do PIS próprio')
    vr_pis_proprio = fields.Dinheiro('Valor do PIS próprio')

    #
    # COFINS própria
    #
    cst_cofins = fields.Selection(ST_COFINS, 'CST COFINS', index=True)
    cst_cofins_entrada = fields.Selection(ST_COFINS_ENTRADA, 'CST COFINS')
    cst_cofins_saida = fields.Selection(ST_COFINS_SAIDA, 'CST COFINS')
    md_cofins_proprio = fields.Selection(MODALIDADE_BASE_COFINS, 'Modalidade BC da COFINS própria',
                                         default=MODALIDADE_BASE_COFINS_ALIQUOTA)
    bc_cofins_proprio = fields.Dinheiro('Base do COFINS próprio')
    al_cofins_proprio = fields.Quantidade('Alíquota da COFINS própria')
    vr_cofins_proprio = fields.Dinheiro('Valor do COFINS próprio')

    #
    # Grupo ISS
    #

    # ISS
    # cst_iss = fields.Selection(ST_ISS, 'CST ISS', index=True)
    bc_iss = fields.Dinheiro('Base do ISS')
    al_iss = fields.Dinheiro('Alíquota do ISS')
    vr_iss = fields.Dinheiro('Valor do ISS')

    #
    # Total da NF e da fatura (podem ser diferentes no caso de operação triangular)
    #
    vr_nf = fields.Dinheiro('Valor da NF')
    vr_fatura = fields.Dinheiro('Valor da fatura')

    al_ibpt = fields.Porcentagem('Alíquota IBPT')
    vr_ibpt = fields.Dinheiro('Valor IBPT')

    # Previdência social
    previdencia_retido = fields.Boolean('INSS retido?', index=True)
    bc_previdencia = fields.Dinheiro('Base do INSS')
    al_previdencia = fields.Porcentagem('Alíquota do INSS')
    vr_previdencia = fields.Dinheiro('Valor do INSS')

    # Informações adicionais
    infcomplementar = fields.Text('Informações complementares')

    #
    # Dados especiais para troca de informações entre empresas
    #
    numero_pedido = fields.Char('Número do pedido', size=15)
    numero_item_pedido = fields.Integer('Número do item pedido')

    #
    # Campos para a validação das entradas
    #
    produto_codigo = fields.Char('Código do produto original', size=60, index=True)
    produto_descricao = fields.Char('Descrição do produto original', size=60, index=True)
    produto_ncm = fields.Char('NCM do produto original', size=60, index=True)
    produto_codigo_barras = fields.Char('Código de barras do produto original', size=60, index=True)
    unidade = fields.Char('Unidade do produto original', size=6, index=True)
    unidade_tributacao = fields.Char('Unidade de tributação do produto original', size=6, index=True)
    fator_quantidade = fields.Float('Fator de conversão da quantidade')
    quantidade_original = fields.Quantidade('Quantidade')
    cfop_original_id = fields.Many2one('sped.cfop', 'CFOP original', index=True)

    credita_icms_proprio = fields.Boolean('Credita ICMS próprio?', index=True)
    credita_icms_st = fields.Boolean('Credita ICMS ST?', index=True)
    informa_icms_st = fields.Boolean('Informa ICMS ST?', index=True)
    credita_ipi = fields.Boolean('Credita IPI?', index=True)
    credita_pis_cofins = fields.Boolean('Credita PIS-COFINS?', index=True)

    #
    # Campos para rateio de custo
    #
    # vr_frete_rateio = fields.function(_get_calcula_custo, type='float', string=u'Valor do frete', store=STORE_CUSTO, digits=(18, 2))
    # vr_seguro_rateio = fields.function(_get_calcula_custo, type='float', string=u'Valor do seguro', store=STORE_CUSTO, digits=(18, 2))
    # vr_outras_rateio = fields.function(_get_calcula_custo, type='float', string=u'Outras despesas acessórias', store=STORE_CUSTO, digits=(18, 2))
    # vr_desconto_rateio = fields.function(_get_calcula_custo, type='float', string=u'Valor do desconto', store=STORE_CUSTO, digits=(18, 2))
    vr_unitario_custo_comercial = fields.Unitario('Custo unitário comercial')
    vr_custo_comercial = fields.Dinheiro('Custo comercial', compute='_compute_custo_comercial', store=True)

    #
    # Diferencial de alíquota
    #
    calcula_difal = fields.Boolean('Calcula diferencial de alíquota?')
    al_interna_destino = fields.Porcentagem('Alíquota interna do estado destino')
    al_difal = fields.Porcentagem('Alíquota diferencial ICMS próprio')
    vr_difal = fields.Dinheiro('Valor do diferencial de alíquota ICMS próprio')

    #
    # Funções para manter a sincronia entre as CSTs do PIS e COFINS para entrada ou saída
    #
    @api.onchange('cst_ipi_entrada')
    def _onchange_cst_ipi_entrada(self):
        self.ensure_one()
        return {'value': {'cst_ipi': self.cst_ipi_entrada}}

    @api.onchange('cst_ipi_saida')
    def _onchange_cst_ipi_saida(self):
        self.ensure_one()
        return {'value': {'cst_ipi': self.cst_ipi_saida}}

    @api.onchange('cst_pis_entrada')
    def _onchange_cst_pis_entrada(self):
        self.ensure_one()
        return {'value': {'cst_pis': self.cst_pis_entrada, 'cst_cofins_entrada': self.cst_pis_entrada}}

    @api.onchange('cst_pis_saida')
    def _onchange_cst_pis_saida(self):
        self.ensure_one()
        return {'value': {'cst_pis': self.cst_pis_saida, 'cst_cofins_saida': self.cst_pis_saida}}

    @api.onchange('cst_cofins_entrada')
    def _onchange_cst_cofins_entrada(self):
        self.ensure_one()
        return {'value': {'cst_cofins': self.cst_cofins_entrada, 'cst_pis_entrada': self.cst_cofins_entrada}}

    @api.onchange('cst_cofins_saida')
    def _onchange_cst_cofins_saida(self):
        self.ensure_one()
        return {'value': {'cst_cofins': self.cst_cofins_saida, 'cst_pis_saida': self.cst_cofins_saida}}

    def _estado_origem_estado_destino_destinatario(self):
        self.ensure_one()

        #
        # Determinamos as UFs de origem e destino
        #
        if self.entrada_saida == ENTRADA_SAIDA_SAIDA:
            estado_origem = self.empresa_id.estado
            estado_destino = self.participante_id.estado

            if self.emissao == TIPO_EMISSAO_PROPRIA:
                destinatario = self.participante_id
            else:
                destinatario = self.empresa_id

        else:
            estado_origem = self.participante_id.estado
            estado_destino = self.empresa_id.estado

            if self.emissao == TIPO_EMISSAO_PROPRIA:
                destinatario = self.empresa_id
            else:
                destinatario = self.participante_id

        return (estado_origem, estado_destino, destinatario)

    @api.onchange('produto_id')
    def _onchange_produto_id(self):
        self.ensure_one()

        if self.emissao == TIPO_EMISSAO_PROPRIA:
            return self._onchange_produto_id_emissao_propria()
        elif self.emissao == TIPO_EMISSAO_TERCEIROS:
            return self._onchange_produto_id_recebimento()

    def _onchange_produto_id_emissao_propria(self):
        self.ensure_one()

        #
        # Aqui determinados o protocolo e o item da operação a ser seguido para a operação,
        # o produto e o NCM em questão
        #
        res = {}
        valores = {}
        res['value'] = valores

        if not self.produto_id:
            return res

        #
        # Validamos alguns dos M2O necessários, vindos do documento
        #
        if not self.empresa_id:
            raise ValidationError('A empresa ativa não foi definida!')

        if not self.participante_id:
            raise ValidationError('O destinatário/remetente não foi informado!')

        if not self.operacao_id:
            raise ValidationError('A operação fiscal não foi informada!')

        #
        # Se já ocorreu o preenchimento da descrição, não sobrepõe
        #
        if not self.produto_descricao:
            valores['produto_descricao'] = self.produto_id.nome

        valores['org_icms'] = self.produto_id.org_icms or ORIGEM_MERCADORIA_NACIONAL
        valores['unidade_id'] = self.produto_id.unidade_id.id

        if self.produto_id.unidade_tributacao_ncm_id:
            valores['unidade_tributacao_id'] = self.produto_id.unidade_tributacao_ncm_id.id
            valores['fator_conversao_unidade_tributacao'] = self.produto_id.fator_conversao_unidade_tributacao_ncm

        else:
            valores['unidade_tributacao_id'] = self.produto_id.unidade_id.id
            valores['fator_conversao_unidade_tributacao'] = 1

        estado_origem, estado_destino, destinatario = self._estado_origem_estado_destino_destinatario()

        if estado_origem == estado_destino:
            posicao_cfop = POSICAO_CFOP_ESTADUAL
        elif estado_origem == 'EX' or estado_destino == 'EX':
            posicao_cfop = POSICAO_CFOP_ESTRANGEIRO
        else:
            posicao_cfop = POSICAO_CFOP_INTERESTADUAL

        #
        # Determinamos o protocolo que vai ser aplicado à situação
        #
        protocolo = None

        if self.produto_id.protocolo_id:
            protocolo = self.produto_id.protocolo_id

        if protocolo is None and self.produto_id.ncm_id and self.produto_id.ncm_id.protocolo_ids:
            busca_protocolo = [
                ('ncm_ids.ncm_id', '=', self.produto_id.ncm_id.id),
                '|',
                ('estado_ids', '=', False),
                ('estado_ids.uf', '=', estado_destino)
            ]
            protocolo_ids = self.env['sped.protocolo.icms'].search(busca_protocolo)

            if len(protocolo_ids) != 0:
                protocolo = protocolo_ids[0]

        if protocolo is None and self.empresa_id.protocolo_id:
            protocolo = self.empresa_id.protocolo_id

        if (not protocolo) or (protocolo is None):
            raise ValidationError('O protocolo não foi definido!')

        #
        # Tratando protocolos que só valem para determinados estados
        # Caso não seja possível usar o protocolo, por restrição dos
        # estados permitidos, usar a família global da empresa
        #
        if len(protocolo.estado_ids) > 0:
            estado_ids = protocolo.estado_ids.search([('uf', '=', estado_destino)])

            #
            # O estado de destino não pertence ao protocolo, usamos então o protocolo
            # padrão da empresa
            #
            if len(estado_ids) == 0 and not self.empresa_id.protocolo_id:
                if self.produto_id.ncm_id:
                    mensagem_erro = 'Não há protocolo padrão para a empresa, e o protocolo “{protocolo}” ' \
                                    'não pode ser usado para o estado “{estado}” (produto “{produto}”, ' \
                                    'NCM “{ncm}”)!'.format(protocolo=protocolo.descricao, estado=estado_destino,
                                                           produto=self.produto_id.nome,
                                                           ncm=self.produto_id.ncm_id.codigo_formatado)
                else:
                    mensagem_erro = 'Não há protocolo padrão para a empresa, e o protocolo “{protocolo}” ' \
                                    'não pode ser usado para o estado “{estado}” ' \
                                    '(produto “{produto}”)!'.format(protocolo=protocolo.descricao,
                                                                    estado=estado_destino, produto=self.produto_id.nome)

                raise ValidationError(mensagem_erro)

            protocolo = self.empresa_id.protocolo_id

        #
        # Determinamos agora qual linha da operação será seguida
        #
        busca_item = [
            ('operacao_id', '=', self.operacao_id.id),
            ('tipo_protocolo', '=', protocolo.tipo),
            ('protocolo_id', '=', protocolo.id),
            ('cfop_id.posicao', '=', posicao_cfop),
            ('contribuinte', '=', self.participante_id.contribuinte),
        ]

        operacao_item_ids = self.operacao_id.item_ids.search(busca_item)

        #
        # Se não houver um item da operação vinculado ao protocolo e ao tipo contribuinte, tentamos
        # sem o contribuinte
        #
        if len(operacao_item_ids) == 0:
            busca_item = [
                ('operacao_id', '=', self.operacao_id.id),
                ('tipo_protocolo', '=', protocolo.tipo),
                ('protocolo_id', '=', protocolo.id),
                ('cfop_id.posicao', '=', posicao_cfop),
                ('contribuinte', '=', False),
            ]

            operacao_item_ids = self.operacao_id.item_ids.search(busca_item)

        #
        # Não encontrou item da operação específico para o protocolo,
        # buscamos então o item genérico, sem protocolo (mas com o contribuinte)
        #
        if len(operacao_item_ids) == 0:
            busca_item = [
                ('operacao_id', '=', self.operacao_id.id),
                ('tipo_protocolo', '=', protocolo.tipo),
                ('protocolo_id', '=', False),
                ('cfop_id.posicao', '=', posicao_cfop),
                ('contribuinte', '=', self.participante_id.contribuinte),
            ]

            operacao_item_ids = self.operacao_id.item_ids.search(busca_item)

        #
        # Ainda não encontrou item da operação específico para o contribuinte,
        # buscamos então o item genérico, sem protocolo nem contribuinte
        #
        if len(operacao_item_ids) == 0:
            busca_item = [
                ('operacao_id', '=', self.operacao_id.id),
                ('tipo_protocolo', '=', protocolo.tipo),
                ('protocolo_id', '=', False),
                ('cfop_id.posicao', '=', posicao_cfop),
                ('contribuinte', '=', False),
            ]

            operacao_item_ids = self.operacao_id.item_ids.search(busca_item)

        #
        # Não tem item da operação mesmo, ou encontrou mais de um possível?
        #
        if len(operacao_item_ids) == 0 or len(operacao_item_ids) > 1:
            if len(operacao_item_ids) == 0:
                mensagem_erro = 'Não há nenhum item genério na operação, nem específico para o protocolo ' \
                                '“{protocolo}”, configurado para operações {estado}!'
            else:
                mensagem_erro = 'Há mais de um item genério na operação, ou mais de um item específico para ' \
                                'o protocolo “{protocolo}”, configurado para operações {estado}!'

            if posicao_cfop == POSICAO_CFOP_ESTADUAL:
                mensagem_erro = mensagem_erro.format(protocolo=protocolo.descricao, estado='dentro do estado')

            elif posicao_cfop == POSICAO_CFOP_INTERESTADUAL:
                mensagem_erro = mensagem_erro.format(protocolo=protocolo.descricao, estado='interestaduais')

            elif posicao_cfop == POSICAO_CFOP_ESTRANGEIRO:
                mensagem_erro = mensagem_erro.format(protocolo=protocolo.descricao, estado='internacionais')

            raise ValidationError(mensagem_erro)

        #
        # Agora que temos o item da operação, definimos os valores do item
        #
        operacao_item = operacao_item_ids[0]

        valores['operacao_item_id'] = operacao_item.id

        #
        # O protocolo alternativo no item da operação força o uso de determinado
        # protocolo, independente de validade no estado ou outras validações
        #
        if operacao_item.protocolo_alternativo_id:
            valores['protocolo_id'] = operacao_item.protocolo_alternativo_id.id

        else:
            valores['protocolo_id'] = protocolo.id

        return res

    @api.onchange('operacao_item_id')
    def _onchange_operacao_item_id(self):
        self.ensure_one()

        res = {}
        valores = {}
        res['value'] = valores

        if not self.operacao_item_id:
            return res

        valores['cfop_id'] = self.operacao_item_id.cfop_id.id
        valores['compoe_total'] = self.operacao_item_id.compoe_total
        valores['movimentacao_fisica'] = self.operacao_item_id.movimentacao_fisica
        # valores['bc_icms_proprio_com_ipi'] = self.operacao_item_id.bc_icms_proprio_com_ipi
        # valores['bc_icms_st_com_ipi'] = self.operacao_item_id.bc_icms_st_com_ipi

        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            valores['cst_icms_sn'] = self.operacao_item_id.cst_icms_sn
            valores['cst_icms'] = False

        else:
            valores['cst_icms'] = self.operacao_item_id.cst_icms
            valores['cst_icms_sn'] = False

        valores['cst_ipi'] = self.operacao_item_id.cst_ipi

        #
        # Busca agora as alíquotas do PIS e COFINS
        #
        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES and self.operacao_item_id.cst_icms_sn != ST_ICMS_SN_OUTRAS:
            #
            # Força a CST do PIS, COFINS e IPI para o SIMPLES
            #
            valores['cst_ipi'] = ''  # NF-e do SIMPLES não destaca IPI nunca, a não ser quando CSOSN 900
            valores['cst_ipi_entrada'] = ''  # NF-e do SIMPLES não destaca IPI nunca, a não ser quando CSOSN 900
            valores['cst_ipi_saida'] = ''  # NF-e do SIMPLES não destaca IPI nunca, a não ser quando CSOSN 900
            al_pis_cofins = self.env.ref('sped.ALIQUOTA_PIS_COFINS_SIMPLES')
            valores['al_pis_cofins_id'] = al_pis_cofins.id

        else:
            #
            # Determina a alíquota do PIS-COFINS:
            # 1º - se o produto tem uma específica
            # 2º - se o NCM tem uma específica
            # 3º - a geral da empresa
            #
            if self.produto_id.al_pis_cofins_id:
                al_pis_cofins = self.produto_id.al_pis_cofins_id
            # elif self.produto_id.ncm_id.al_pis_cofins_id:
                # al_pis_cofins = self.produto_id.ncm_id.al_pis_cofins_id
            else:
                al_pis_cofins = self.empresa_id.al_pis_cofins_id

            #
            # Se por acaso a CST do PIS-COFINS especificada no item da operação
            # definir que não haverá cobrança de PIS-COFINS, usa a CST da operação
            # caso contrário, usa a definida acima
            #
            if (self.operacao_item_id.al_pis_cofins_id
                and not (
                    self.operacao_item_id.al_pis_cofins_id.cst_pis_cofins_saida in ST_PIS_CALCULA_ALIQUOTA
                    or self.operacao_item_id.al_pis_cofins_id.cst_pis_cofins_saida in ST_PIS_CALCULA_QUANTIDADE
                )):
                al_pis_cofins = self.operacao_item_id.al_pis_cofins_id

            valores['al_pis_cofins_id'] = al_pis_cofins.id

        #
        # Busca a alíquota do IBPT quando venda
        #
        if self.operacao_item_id.cfop_id.eh_venda:
            if self.produto_id.ncm_id:
                ibpt = self.env['sped.ibptax.ncm']

                ibpt_ids = ibpt.search([
                    ('estado_id', '=', self.empresa_id.municipio_id.estado_id.id),
                    ('ncm_id', '=', self.produto_id.ncm_id.id),
                ])

                if len(ibpt_ids) > 0:
                    valores['al_ibpt'] = ibpt_ids[0].al_ibpt_nacional + ibpt_ids[0].al_ibpt_estadual

                    if self.operacao_item_id.cfop_id.posicao == POSICAO_CFOP_ESTRANGEIRO:
                        valores['al_ibpt'] += ibpt_ids[0].al_ibpt_internacional

            #
            # NBS por ser mais detalhado tem prioridade sobre o código do serviço
            #
            elif self.produto_id.nbs_id:
                ibpt = self.env['sped.ibptax.nbs']

                ibpt_ids = ibpt.search([
                    ('estado_id', '=', self.empresa_id.municipio_id.estado_id.id),
                    ('nbs_id', '=', self.produto_id.nbs_id.id),
                ])

                if len(ibpt_ids) > 0:
                    valores['al_ibpt'] = ibpt_ids[0].al_ibpt_nacional + ibpt_ids[0].al_ibpt_municipal

                    if self.operacao_item_id.cfop_id.posicao == POSICAO_CFOP_ESTRANGEIRO:
                        valores['al_ibpt'] += ibpt_ids[0].al_ibpt_internacional

            elif self.produto_id.servico_id:
                ibpt = self.env['sped.ibptax.servico']

                ibpt_ids = ibpt.search([
                    ('estado_id', '=', self.empresa_id.municipio_id.estado_id.id),
                    ('servico_id', '=', self.produto_id.servico_id.id),
                ])

                if len(ibpt_ids) > 0:
                    valores['al_ibpt'] = ibpt_ids[0].al_ibpt_nacional + ibpt_ids[0].al_ibpt_municipal

                    if self.operacao_item_id.cfop_id.posicao == POSICAO_CFOP_ESTRANGEIRO:
                        valores['al_ibpt'] += ibpt_ids[0].al_ibpt_internacional

        return res

    @api.onchange('cfop_id')
    def _onchange_cfop_id(self):
        self.ensure_one()

        res = {}
        valores = {}
        res['value'] = valores

        if not self.cfop_id:
            return res

        valores['al_simples'] = 0
        valores['calcula_difal'] = False
        valores['bc_icms_proprio_com_ipi'] = False
        valores['bc_icms_st_com_ipi'] = False

        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            if self.cfop_id.calcula_simples_csll_irpj:
                valores['al_simples'] = self.empresa_id.simples_aliquota_id.al_simples

        else:
            if self.consumidor_final == TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL and self.cfop_id.eh_venda:
                valores['calcula_difal'] = True
                valores['bc_icms_proprio_com_ipi'] = True
                valores['bc_icms_st_com_ipi'] = True

        return res

    @api.onchange('al_pis_cofins_id')
    def _onchange_al_pis_cofins_id(self):
        self.ensure_one()

        res = {}
        valores = {}
        res['value'] = valores

        if not self.al_pis_cofins_id:
            return res

        valores['md_pis_proprio'] = self.al_pis_cofins_id.md_pis_cofins
        valores['al_pis_proprio'] = self.al_pis_cofins_id.al_pis or 0

        valores['md_cofins_proprio'] = self.al_pis_cofins_id.md_pis_cofins
        valores['al_cofins_proprio'] = self.al_pis_cofins_id.al_cofins or 0

        if self.entrada_saida == ENTRADA_SAIDA_ENTRADA:
            valores['cst_pis'] = self.al_pis_cofins_id.cst_pis_cofins_entrada
            valores['cst_cofins'] = self.al_pis_cofins_id.cst_pis_cofins_entrada
            valores['cst_pis_entrada'] = self.al_pis_cofins_id.cst_pis_cofins_entrada
            valores['cst_cofins_entrada'] = self.al_pis_cofins_id.cst_pis_cofins_entrada

        else:
            valores['cst_pis'] = self.al_pis_cofins_id.cst_pis_cofins_saida
            valores['cst_cofins'] = self.al_pis_cofins_id.cst_pis_cofins_saida
            valores['cst_pis_saida'] = self.al_pis_cofins_id.cst_pis_cofins_saida
            valores['cst_cofins_saida'] = self.al_pis_cofins_id.cst_pis_cofins_saida

        return res

    @api.onchange('cst_ipi')
    def _onchange_cst_ipi(self):
        self.ensure_one()

        res = {}
        valores = {}
        res['value'] = valores

        if not self.cst_ipi:
            return res

        #
        # Na nota de terceiros, respeitamos o IPI enviado no XML original, e não recalculamos
        #
        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES and self.cst_icms_sn != ST_ICMS_SN_OUTRAS:
            valores['cst_ipi'] = ''  # NF-e do SIMPLES não destaca IPI nunca
            valores['cst_ipi_entrada'] = ''  # NF-e do SIMPLES não destaca IPI nunca
            valores['cst_ipi_saida'] = ''  # NF-e do SIMPLES não destaca IPI nunca
            valores['md_ipi'] = MODALIDADE_BASE_IPI_ALIQUOTA
            valores['bc_ipi'] = 0
            valores['al_ipi'] = 0
            valores['vr_ipi'] = 0
            return res

        #
        # Determina a alíquota do IPI:
        # 1º - se o produto tem uma específica
        # 2º - se o NCM tem uma específica
        #
        if self.produto_id.al_ipi_id:
            al_ipi = self.produto_id.al_ipi_id
        elif self.produto_id.ncm_id.al_ipi_id:
            al_ipi = self.produto_id.ncm_id.al_ipi_id
        else:
            al_ipi = None

        if (self.cst_ipi not in ST_IPI_CALCULA) or (not al_ipi) or (al_ipi is None):
            valores['md_ipi'] = MODALIDADE_BASE_IPI_ALIQUOTA
            valores['bc_ipi'] = 0
            valores['al_ipi'] = 0
            valores['vr_ipi'] = 0

        else:
            valores['md_ipi'] = al_ipi.md_ipi
            valores['al_ipi'] = al_ipi.al_ipi

        return res

    @api.onchange('protocolo_id', 'cfop_id', 'calcula_difal', 'org_icms', 'cst_icms', 'cst_icms_sn', 'produto_id')
    def _onchange_cst_icms_cst_icms_sn(self):
        self.ensure_one()

        res = {}
        valores = {}
        res['value'] = valores
        avisos = {}
        res['warning'] = avisos

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        if not self.protocolo_id:
            return res

        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            if self.cst_icms_sn in ST_ICMS_SN_CALCULA_CREDITO:
                if not self.cfop_id.eh_venda:
                    avisos['title'] = 'Aviso!'
                    avisos[
                        'message'] = 'Você selecionou uma CSOSN que dá direito a crédito, ' \
                                     'porém a CFOP não indica uma venda!'

                valores['al_icms_sn'] = self.empresa_id.simples_aliquota_id.al_icms

            else:
                valores['al_icms_sn'] = 0
                valores['rd_icms_sn'] = 0

        else:
            valores['al_icms_sn'] = 0
            valores['rd_icms_sn'] = 0

        estado_origem, estado_destino, destinatario = self._estado_origem_estado_destino_destinatario()

        #
        # Agora, buscamos as alíquotas necessárias
        #
        aliquota_origem_destino = self.protocolo_id.busca_aliquota(estado_origem, estado_destino, self.data_emissao,
                                                                   self.empresa_id)

        #
        # Alíquota do ICMS próprio
        #
        if self.org_icms in ORIGEM_MERCADORIA_ALIQUOTA_4 and self.cfop_id.posicao == POSICAO_CFOP_INTERESTADUAL:
            al_icms = self.env.ref('sped.ALIQUOTA_ICMS_PROPRIO_4')

        else:
            al_icms = aliquota_origem_destino.al_icms_proprio_id

        valores['md_icms_proprio'] = al_icms.md_icms
        valores['pr_icms_proprio'] = al_icms.pr_icms
        valores['rd_icms_proprio'] = al_icms.rd_icms
        valores['al_icms_proprio'] = al_icms.al_icms
        valores['al_interna_destino'] = 0
        valores['al_difal'] = 0

        if self.calcula_difal:
            aliquota_interna_destino = self.protocolo_id.busca_aliquota(estado_destino, estado_destino,
                                                                        self.data_emissao, self.empresa_id)

            if aliquota_interna_destino.al_icms_proprio_id.al_icms > al_icms.al_icms:
                al_difal = aliquota_interna_destino.al_icms_proprio_id.al_icms
                al_difal -= al_icms.al_icms

                valores['al_difal'] = al_difal
                valores['al_interna_destino'] = aliquota_interna_destino.al_icms_proprio_id.al_icms

        #
        # Alíquota e MVA do ICMS ST, somente para quando não houver serviço
        # (serviço pode ter ICMS na nota conjugada [DF])
        #
        if ((self.cst_icms in ST_ICMS_CALCULA_ST or self.cst_icms_sn in ST_ICMS_SN_CALCULA_ST)
            and self.produto_id.tipo != TIPO_PRODUTO_SERVICO_SERVICOS):
            al_icms_st = aliquota_origem_destino.al_icms_st_id

            valores['md_icms_st'] = al_icms_st.md_icms
            valores['pr_icms_st'] = al_icms_st.pr_icms
            valores['rd_icms_st'] = al_icms_st.rd_icms
            valores['al_icms_st'] = al_icms_st.al_icms

            #
            # Verificamos a necessidade de se busca a MVA (ajustada ou não)
            #
            if al_icms_st.md_icms == MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO and (not al_icms_st.pr_icms):
                protocolo_ncm = self.produto_id.ncm_id.busca_mva(self.protocolo_id)

                if (protocolo_ncm is not None) and protocolo_ncm:
                    pr_icms_st = protocolo_ncm.mva

                    #
                    # SIMPLES não ajusta a MVA
                    #
                    # Atenção aqui, pois SC determina que é o regime tributário do destinatário que determina o ajuste
                    #
                    ajusta_mva = False
                    if (estado_origem == 'SC' or estado_destino == 'SC'):
                        if destinatario.regime_tributario != REGIME_TRIBUTARIO_SIMPLES:
                            ajusta_mva = True

                    elif self.regime_tributario != REGIME_TRIBUTARIO_SIMPLES:
                        ajusta_mva = True

                    if ajusta_mva:
                        al_icms_proprio = 100 - al_icms.al_icms
                        al_icms_proprio /= 100

                        al_icms_st = 100 - al_icms_st.al_icms
                        al_icms_st /= 100

                        pr_icms_st /= 100
                        pr_icms_st += 1
                        pr_icms_st *= al_icms_proprio / al_icms_st
                        pr_icms_st -= 1
                        pr_icms_st *= 100
                        pr_icms_st = pr_icms_st.quantize(D('0.0001'))

                    valores['pr_icms_st'] = pr_icms_st

        return res

    @api.onchange('vr_unitario', 'quantidade', 'vr_unitario_tributacao', 'quantidade_tributacao', 'vr_frete',
                  'vr_seguro', 'vr_desconto', 'vr_outras', 'vr_ii', 'fator_conversao_unidade_tributacao')
    def _onchange_calcula_valor_operacao(self):
        self.ensure_one()

        res = {}
        valores = {}
        res['value'] = valores

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        #
        # Cupom Fiscal só aceita até 3 casas decimais no valor unitário
        #
        if self.modelo == '2D':
            self.vr_unitario = self.vr_unitario.quantize(D('0.001'))
            self.vr_unitario_tributacao = self.vr_unitario_tributacao.quantize(D('0.001'))

            valores['vr_unitario'] = self.vr_unitario
            valores['vr_unitario_tributacao'] = self.vr_unitario_tributacao

        #
        # Calcula o valor dos produtos
        #
        vr_produtos = self.quantidade * self.vr_unitario
        vr_produtos = vr_produtos.quantize(D('0.01'))

        #
        # Até segunda ordem, a quantidade e valor unitário para tributação não mudam
        #
        quantidade_tributacao = self.quantidade * self.fator_conversao_unidade_tributacao
        vr_unitario_tributacao = vr_produtos / quantidade_tributacao
        vr_unitario_tributacao = vr_unitario_tributacao.quantize(D('0.0000000001'))
        vr_produtos_tributacao = quantidade_tributacao * vr_unitario_tributacao
        vr_produtos_tributacao = vr_produtos_tributacao
        valores['quantidade_tributacao'] = quantidade_tributacao
        valores['vr_unitario_tributacao'] = vr_unitario_tributacao

        vr_operacao = vr_produtos + self.vr_frete + self.vr_seguro + self.vr_outras - self.vr_desconto
        vr_operacao_tributacao = vr_produtos_tributacao + self.vr_frete + self.vr_seguro + self.vr_outras - \
                                 self.vr_desconto + self.vr_ii

        valores['vr_produtos'] = vr_produtos
        valores['vr_produtos_tributacao'] = vr_produtos_tributacao
        valores['vr_operacao'] = vr_operacao
        valores['vr_operacao_tributacao'] = vr_operacao_tributacao

        return res

    @api.onchange('vr_operacao_tributacao', 'quantidade_tributacao', 'cst_ipi', 'md_ipi', 'bc_ipi', 'al_ipi', 'vr_ipi')
    def _onchange_calcula_ipi(self):
        res = {}
        valores = {}
        res['value'] = valores

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        valores['bc_ipi'] = 0
        valores['vr_ipi'] = 0

        #
        # SIMPLES não tem IPI
        #
        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            valores['cst_ipi'] = ''
            valores['md_ipi'] = MODALIDADE_BASE_IPI_ALIQUOTA
            valores['al_ipi'] = 0
            return res

        if self.cst_ipi not in ST_IPI_CALCULA:
            valores['al_ipi'] = 0
            return res

        bc_ipi = D(0)
        vr_ipi = D(0)

        if self.md_ipi == MODALIDADE_BASE_IPI_ALIQUOTA:
            bc_ipi = self.vr_operacao_tributacao
            vr_ipi = bc_ipi * self.al_ipi / 100

        elif self.md_ipi == MODALIDADE_BASE_IPI_QUANTIDADE:
            bc_ipi = 0
            vr_ipi = self.quantidade_tributacao * self.al_ipi

        vr_ipi = vr_ipi.quantize(D('0.01'))

        valores['bc_ipi'] = bc_ipi
        valores['vr_ipi'] = vr_ipi

        return res

    @api.onchange('vr_operacao_tributacao', 'rd_icms_sn', 'cst_icms_sn', 'al_icms_sn', 'vr_icms_sn')
    def _onchange_calcula_icms_sn(self):
        res = {}
        valores = {}
        res['value'] = valores

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        valores['vr_icms_sn'] = 0

        #
        # Só SIMPLES tem crédito de ICMS SN
        #
        if self.regime_tributario != REGIME_TRIBUTARIO_SIMPLES:
            valores['cst_icms_sn'] = False
            valores['rd_icms_sn'] = 0
            valores['al_icms_sn'] = 0
            return res

        if self.cst_icms_sn not in ST_ICMS_SN_CALCULA_CREDITO:
            valores['rd_icms_sn'] = 0
            valores['al_icms_sn'] = 0
            return res

        al_icms_sn = self.al_icms_sn

        #
        # Aplica a redução da alíquota quando houver
        #
        if self.rd_icms_sn:
            al_icms_sn = al_icms_sn - (al_icms_sn * self.rd_icms_sn / 100)
            al_icms_sn = al_icms_sn.quantize(D('0.01'))

        vr_icms_sn = self.vr_operacao_tributacao * al_icms_sn / 100
        vr_icms_sn = vr_icms_sn.quantize(D('0.01'))

        valores['vr_icms_sn'] = vr_icms_sn

        return res

    @api.onchange('vr_operacao_tributacao', 'quantidade_tributacao', 'cst_pis', 'cst_cofins', 'md_pis_proprio',
                  'md_cofins_proprio', 'bc_pis_proprio', 'al_pis_proprio', 'vr_pis_proprio', 'bc_cofins_proprio',
                  'al_cofins_proprio', 'vr_cofins_proprio')
    def _onchange_calcula_pis_cofins(self):
        res = {}
        valores = {}
        res['value'] = valores

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        valores['md_pis_proprio'] = MODALIDADE_BASE_PIS_ALIQUOTA
        valores['bc_pis_proprio'] = 0
        valores['al_pis_proprio'] = 0
        valores['vr_pis_proprio'] = 0

        valores['md_cofins_proprio'] = MODALIDADE_BASE_COFINS_ALIQUOTA
        valores['bc_cofins_proprio'] = 0
        valores['al_cofins_proprio'] = 0
        valores['vr_cofins_proprio'] = 0

        if self.cst_pis in ST_PIS_CALCULA or self.cst_pis in ST_PIS_CALCULA_CREDITO:
            if self.cst_pis in ST_PIS_CALCULA_ALIQUOTA:
                md_pis_proprio = MODALIDADE_BASE_PIS_ALIQUOTA
                bc_pis_proprio = self.vr_operacao_tributacao
                vr_pis_proprio = bc_pis_proprio * (self.al_pis_proprio / 100)

                md_cofins_proprio = MODALIDADE_BASE_COFINS_ALIQUOTA
                bc_cofins_proprio = self.vr_operacao_tributacao
                vr_cofins_proprio = bc_cofins_proprio * (self.al_cofins_proprio / 100)

            else:
                md_pis_proprio = MODALIDADE_BASE_PIS_QUANTIDADE
                bc_pis_proprio = 0
                vr_pis_proprio = self.quantidade_tributacao * self.al_pis_proprio

                md_cofins_proprio = MODALIDADE_BASE_COFINS_QUANTIDADE
                bc_cofins_proprio = 0
                vr_cofins_proprio = self.quantidade_tributacao * self.al_cofins_proprio

            vr_pis_proprio = vr_pis_proprio.quantize(D('0.01'))
            vr_cofins_proprio = vr_cofins_proprio.quantize(D('0.01'))

            valores['md_pis_proprio'] = md_pis_proprio
            valores['bc_pis_proprio'] = bc_pis_proprio
            valores['al_pis_proprio'] = self.al_pis_proprio
            valores['vr_pis_proprio'] = vr_pis_proprio

            valores['md_cofins_proprio'] = md_cofins_proprio
            valores['bc_cofins_proprio'] = bc_cofins_proprio
            valores['al_cofins_proprio'] = self.al_cofins_proprio
            valores['vr_cofins_proprio'] = vr_cofins_proprio

        return res

    @api.onchange('vr_operacao_tributacao', 'quantidade_tributacao', 'vr_ipi', 'vr_outras',
                  'cst_icms', 'cst_icms_sn',
                  'md_icms_proprio', 'pr_icms_proprio', 'rd_icms_proprio', 'bc_icms_proprio_com_ipi', 'bc_icms_proprio', 'al_icms_proprio', 'vr_icms_proprio',
                  'md_icms_st', 'pr_icms_st', 'rd_icms_st', 'bc_icms_st_com_ipi',
                  'bc_icms_st', 'al_icms_st', 'vr_icms_st',
                  'calcula_difal'
                  )
    def _onchange_calcula_icms(self):
        self.ensure_one()

        res = {}
        valores = {}
        res['value'] = valores

        self._onchange_calcula_icms_proprio(valores)
        self._onchange_calcula_icms_st(valores)

        return res

    def _onchange_calcula_icms_proprio(self, valores):
        self.ensure_one()

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return

        valores['bc_icms_proprio'] = 0
        valores['vr_icms_proprio'] = 0

        #
        # Baseado no valor da situação tributária, calcular o ICMS próprio
        #
        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            if not ((self.cst_icms_sn in ST_ICMS_SN_CALCULA_ST)
               or (self.cst_icms_sn in ST_ICMS_SN_CALCULA_PROPRIO)
               or (self.cst_icms_sn == ST_ICMS_SN_ANTERIOR)):
                return

        else:
            if self.cst_icms not in ST_ICMS_CALCULA_PROPRIO:
                return

        if not self.md_icms_proprio:
            return

        if self.md_icms_proprio in (
                MODALIDADE_BASE_ICMS_PROPRIO_PAUTA, MODALIDADE_BASE_ICMS_PROPRIO_PRECO_TABELADO_MAXIMO):
            bc_icms_proprio = self.quantidade_tributacao * self.pr_icms_proprio

        else:
            bc_icms_proprio = self.vr_operacao_tributacao

        #
        # Nas notas de importação o ICMS é "por fora"
        #
        if self.cfop_id.posicao == POSICAO_CFOP_ESTRANGEIRO and self.entrada_saida == ENTRADA_SAIDA_ENTRADA:
            bc_icms_proprio = bc_icms_proprio / D(1 - self.al_icms_proprio / D(100))

        #
        # Nas devoluções de compra de empresa que não destaca IPI, o valor do IPI é
        # informado em outras depesas acessórias;
        # nesses casos, inverter a consideração da soma do valor do IPI, pois o valor
        # de outras despesas já entrou no valor tributável
        #
        if self.cfop_id.eh_devolucao_compra or self.cfop_id.eh_retorno_saida:
            if not self.bc_icms_proprio_com_ipi:
                if (not self.vr_ipi) and self.vr_outras:
                    bc_icms_proprio -= self.vr_outras

        elif self.bc_icms_proprio_com_ipi:
            bc_icms_proprio += self.vr_ipi

        #
        # Agora que temos a base final, aplicamos a margem caso necessário
        #
        if self.md_icms_proprio == MODALIDADE_BASE_ICMS_PROPRIO_MARGEM_VALOR_AGREGADO:
            bc_icms_proprio = bc_icms_proprio * (1 + (self.pr_icms_proprio / 100))

        #
        # Vai haver redução da base de cálculo?
        # Aqui também, no caso da situação 30 e 60, calculamos a redução, quando houver
        #
        if self.cst_icms in ST_ICMS_COM_REDUCAO or self.cst_icms_sn in ST_ICMS_SN_CALCULA_ST:
            bc_icms_proprio = bc_icms_proprio.quantize(D('0.01'))
            bc_icms_proprio = bc_icms_proprio * (1 - (self.rd_icms_proprio / 100))

        bc_icms_proprio = bc_icms_proprio.quantize(D('0.01'))

        vr_icms_proprio = bc_icms_proprio * (self.al_icms_proprio / 100)
        vr_icms_proprio = vr_icms_proprio.quantize(D('0.01'))

        valores['bc_icms_proprio'] = bc_icms_proprio
        valores['vr_icms_proprio'] = vr_icms_proprio

    def _onchange_calcula_icms_st(self, valores):
        self.ensure_one()

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return

        valores['bc_icms_st'] = 0
        valores['vr_icms_st'] = 0

        #
        # Baseado no valor da situação tributária, calcular o ICMS ST
        #
        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            if self.cst_icms_sn not in ST_ICMS_SN_CALCULA_ST:
                return

        else:
            if self.cst_icms not in ST_ICMS_CALCULA_ST:
                return

        if not self.md_icms_st:
            return

        if self.md_icms_st == MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO:
            bc_icms_st = self.vr_operacao_tributacao

        else:
            bc_icms_st = self.vr_operacao_tributacao

        #
        # Nas devoluções de compra de empresa que não destaca IPI, o valor do IPI é
        # informado em outras depesas acessórias;
        # nesses casos, inverter a consideração da soma do valor do IPI, pois o valor
        # de outras despesas já entrou no valor tributável
        #
        if self.cfop_id.eh_devolucao_compra:
            if not self.bc_icms_st_com_ipi:
                if (not self.vr_ipi) and self.vr_outras:
                    bc_icms_st -= self.vr_outras

        elif self.bc_icms_st_com_ipi:
            bc_icms_st += self.vr_ipi

        #
        # Agora que temos a base final, aplicamos a margem caso necessário
        #
        if self.md_icms_st == MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO:
            bc_icms_st = bc_icms_st * (1 + (self.pr_icms_st / 100))

        #
        # Vai haver redução da base de cálculo?
        #
        if self.rd_icms_st:
            bc_icms_st = bc_icms_st.quantize(D('0.01'))
            bc_icms_st = bc_icms_st * (1 - (self.rd_icms_st / 100))

        bc_icms_st = bc_icms_st.quantize(D('0.01'))

        vr_icms_st = bc_icms_st * (self.al_icms_st / 100)
        vr_icms_st = vr_icms_st.quantize(D('0.01'))
        vr_icms_st -= self.vr_icms_proprio

        valores['bc_icms_st'] = bc_icms_st
        valores['vr_icms_st'] = vr_icms_st

        if ((self.cst_icms in ST_ICMS_ZERA_ICMS_PROPRIO)
            or ((self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES)
            and (self.cst_icms_sn not in ST_ICMS_SN_CALCULA_PROPRIO)
            and (self.cst_icms_sn not in ST_ICMS_SN_CALCULA_ST))):
            valores['bc_icms_proprio'] = 0
            valores['vr_icms_proprio'] = 0

    @api.onchange('vr_operacao_tributacao', 'calcula_difal', 'al_icms_proprio', 'al_interna_destino')
    def _onchange_calcula_difal(self):
        self.ensure_one()

        res = {}
        valores = {}
        res['value'] = valores

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        valores['al_difal'] = 0
        valores['vr_difal'] = 0

        if self.calcula_difal:
            al_difal = self.al_interna_destino - self.al_icms_proprio
            vr_difal = self.vr_operacao_tributacao * al_difal / 100
            vr_difal = vr_difal.quantize(D('0.01'))
            valores['al_difal'] = al_difal
            valores['vr_difal'] = vr_difal

        return res

    @api.onchange('vr_fatura', 'al_simples')
    def _onchange_calcula_simples(self):
        self.ensure_one()

        res = {}
        valores = {}
        res['value'] = valores

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        if self.al_simples:
            vr_simples = self.vr_fatura * self.al_simples / 100
            vr_simples = vr_simples.quantize(D('0.01'))
            valores['vr_simples'] = vr_simples

        return res

    @api.onchange('vr_operacao_tributacao', 'al_ibpt')
    def _onchange_calcula_ibpt(self):
        self.ensure_one()

        res = {}
        valores = {}
        res['value'] = valores

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        if self.al_ibpt:
            vr_ibpt = self.vr_operacao_tributacao * self.al_ibpt / 100
            vr_ibpt = vr_ibpt.quantize(D('0.01'))
            valores['vr_ibpt'] = vr_ibpt

        return res

    @api.onchange('vr_operacao', 'vr_icms_proprio', 'vr_icms_st', 'vr_ipi', 'vr_ii')
    def _onchange_calcula_total(self):
        self.ensure_one()

        res = {}
        valores = {}
        res['value'] = valores

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        vr_nf = self.vr_operacao + self.vr_ipi + self.vr_icms_st + self.vr_ii

        #
        # Nas importações o ICMS é somado no total da nota
        #
        if self.vr_ii > 0:
            vr_nf += self.vr_icms_proprio

        valores['vr_nf'] = vr_nf

        if self.compoe_total:
            valores['vr_fatura'] = vr_nf

        else:
            #
            # Não concordo com o valor do item não compor o total da NF, mas enfim...
            #
            valores['vr_nf'] = 0
            valores['vr_fatura'] = 0

        return res

    @api.depends('vr_nf', 'vr_simples', 'vr_difal', 'vr_icms_proprio', 'vr_icms_sn', 'credita_icms_proprio',
                 'cfop_id', 'vr_ipi', 'credita_ipi', 'vr_pis_proprio', 'vr_cofins_proprio',
                 'credita_pis_cofins')
    def _compute_custo_comercial(self):
        for item in self:
            vr_custo = item.vr_nf
    
            if item.emissao == TIPO_EMISSAO_PROPRIA:
                vr_custo += item.vr_simples
    
            vr_custo += item.vr_difal
    
            #
            # Abate do custo os créditos de impostos
            #
            if item.entrada_saida == ENTRADA_SAIDA_ENTRADA:
                if item.credita_icms_proprio and (item.vr_icms_proprio or item.vr_icms_sn):
                    #
                    # Crédito de ICMS para compra do ativo imobilizado é recebido em 48 ×
                    # por isso, como a empresa pode não receber esse crédito de fato,
                    # não considera o abatimento do crédito na formação do custo
                    #
                    if not item.cfop_id.eh_compra_ativo:
                        vr_custo -= item.vr_icms_proprio
                        vr_custo -= item.vr_icms_sn
    
                if item.credita_ipi and item.vr_ipi:
                    vr_custo -= item.vr_ipi
    
                if item.credita_pis_cofins and (item.vr_pis_proprio or item.vr_cofins_proprio):
                    vr_custo -= item.vr_pis_proprio
                    vr_custo -= item.vr_cofins_proprio
    
                # if item_obj.documento_id.vr_produtos is not None \
                #         and item_obj.documento_id.vr_produtos > 0 \
                #         and item_obj.vr_produtos is not None \
                #         and item_obj.vr_produtos > 0:
                #     proporcao_item = D(item_obj.vr_produtos or 0) / D(item_obj.documento_id.vr_produtos or 0)
                # else:
                #     proporcao_item = D('0')
                #
                # vr_frete_rateio = D('0')
                # vr_seguro_rateio = D('0')
                # vr_outras_rateio = D('0')
                # vr_desconto_rateio = D('0')
                #
                # #
                # # Ajusta o rateio dos valores avulsos
                # #
                # if item_obj.documento_id.vr_frete_rateio:
                #     vr_frete_rateio = D(item_obj.documento_id.vr_frete_rateio or 0) * proporcao_item
                #     vr_custo += vr_frete_rateio
                # if item_obj.documento_id.vr_seguro_rateio:
                #     vr_seguro_rateio = D(item_obj.documento_id.vr_seguro_rateio or 0) * proporcao_item
                #     vr_custo += vr_seguro_rateio
                # if item_obj.documento_id.vr_desconto_rateio:
                #     vr_desconto_rateio = D(item_obj.documento_id.vr_desconto_rateio or 0) * proporcao_item
                #     vr_custo -= vr_desconto_rateio
                # if item_obj.documento_id.vr_outras_rateio:
                #     vr_outras_rateio = D(item_obj.documento_id.vr_outras_rateio or 0) * proporcao_item
                #     vr_custo += vr_outras_rateio
                #
                # vr_custo = vr_custo.quantize(D('0.01'))
                #
                # if item_obj.quantidade_estoque:
                #     vr_unitario_custo = vr_custo / D(item_obj.quantidade_estoque or 0)
                #     vr_unitario_custo = vr_unitario_custo.quantize(D('0.0000000001'))
                # else:
                #     vr_unitario_custo = D('0')
                #
                # if nome_campo == 'vr_custo':
                #     res[item_obj.id] = vr_custo
                # elif nome_campo == 'vr_unitario_custo':
                #     res[item_obj.id] = vr_unitario_custo
                # elif nome_campo == 'vr_frete_rateio':
                #     res[item_obj.id] = vr_frete_rateio
                # elif nome_campo == 'vr_seguro_rateio':
                #     res[item_obj.id] = vr_seguro_rateio
                # elif nome_campo == 'vr_outras_rateio':
                #     res[item_obj.id] = vr_outras_rateio
                # elif nome_campo == 'vr_desconto_rateio':
                #     res[item_obj.id] = vr_desconto_rateio

            item.vr_custo_comercial = vr_custo
