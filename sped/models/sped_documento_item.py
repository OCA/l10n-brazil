# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from ..constante_tributaria import *
from pybrasil.data import parse_datetime


class DocumentoItem(models.Model):
    _description = 'Item do Documento Fiscal'
    _name = 'sped.documento.item'
    #_order = 'emissao, modelo, data_emissao desc, serie, numero'
    #_rec_name = 'numero'

    documento_id = fields.Many2one('sped.documento', 'Documento', ondelete='cascade', required=True)
    regime_tributario = fields.Selection(REGIME_TRIBUTARIO, 'Regime tributário', default=REGIME_TRIBUTARIO_SIMPLES, related='documento_id.regime_tributario')
    modelo = fields.Selection(MODELO_FISCAL, 'Modelo', related='documento_id.modelo')
    partner_id = fields.Many2one('res.partner', 'Destinatário/Remetente', related='documento_id.partner_id')
    contribuinte = fields.Selection(IE_DESTINATARIO, string='Contribuinte', default=INDICADOR_IE_DESTINATARIO_ISENTO, related='partner_id.contribuinte')

    #company_id = fields.Many2one('res.company', 'Empresa', ondelete='restrict', related='documento_id.company_id')
    #emissao = fields.Selection(TIPO_EMISSAO, 'Tipo de emissão', related='documento_id.emissao')
    #modelo = fields.Selection(MODELO_FISCAL, 'Modelo', related='documento_id.modelo')
    #data_hora_emissao = fields.Datetime('Data de emissão', related='documento_id.data_hora_emissao')
    #data_hora_entrada_saida = fields.Datetime('Data de entrada/saída', related='documento_id.data_hora_entrada_saida')
    #data_emissao = fields.Date('Data de emissão', related='documento_id.data_emissao')
    #hora_emissao = fields.Char('Hora de emissão', size=8, related='documento_id.hora_emissao')
    #data_entrada_saida = fields.Date('Data de entrada/saída', related='documento_id.data_entrada_saida')
    #hora_entrada_saida = fields.Char('Hora de entrada/saída', size=8, related='documento_id.hora_entrada_saida')
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
    compoe_total = fields.Boolean('Compõe o valor total da NF-e?', index=True, default=True)
    movimentacao_fisica = fields.Boolean('Há movimentação física do produto?', default=True)

    # Dados do produto/serviço
    #product_id = fields.Many2one('product.product', 'Produto/Serviço', ondelete='restrict', index=True)
    #uom_id = fields.related('produto_id', 'uom_id', type='Many2one', relation='product.uom', string=u'Unidade', index=True)
    product_id = fields.Many2one('cadastro.produto', 'Produto/Serviço', ondelete='restrict', index=True)
    uom_id = fields.Many2one('cadastro.unidade', 'Unidade', related='product_id.unidade_id')
    quantidade = fields.Quantidade('Quantidade', default=1)
    # 'unidade' = models.ForeignKey('cadastro.Unidade', verbose_name=_('unidade'), related_name=u'fis_notafiscalitem_unidade', null=True, blank=True)
    vr_unitario = fields.Unitario('Valor unitário')

    # Quantidade de tributação
    quantidade_tributacao = fields.Quantidade('Quantidade para tributação')
    # 'unidade_tributacao' = models.ForeignKey('cadastro.Unidade', verbose_name=_('unidade para tributação'), related_name=u'fis_notafiscalitem_unidade_tributacao', blank=True, null=True)
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
    #contribuinte = fields.related('partner_id', 'contribuinte', type='char', string=u'Contribuinte', store=False, index=True)
    org_icms = fields.Selection(ORIGEM_MERCADORIA, 'Origem da mercadoria', index=True, default=ORIGEM_MERCADORIA_NACIONAL)
    cst_icms = fields.Selection(ST_ICMS, 'Situação tributária do ICMS', index=True, default=ST_ICMS_ISENTA)
    partilha = fields.Boolean('Partilha de ICMS entre estados (CST 10 ou 90)?')
    al_bc_icms_proprio_partilha = fields.Porcentagem('% da base de cálculo da operação própria')
    uf_partilha_id = fields.Many2one('sped.estado', 'Estado para o qual é devido o ICMS ST', index=True)
    repasse = fields.Boolean('Repasse de ICMS retido anteriosvente entre estados (CST 41)?', index=True)
    md_icms_proprio = fields.Selection(MODALIDADE_BASE_ICMS_PROPRIO, 'Modalidade da base de cálculo do ICMS próprio', default=MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO)
    pr_icms_proprio = fields.Quantidade('Parâmetro do ICMS próprio')
    rd_icms_proprio = fields.Porcentagem('% de redução da base de cálculo do ICMS próprio')
    bc_icms_proprio_com_ipi = fields.Boolean('IPI integra a base do ICMS próprio?')
    bc_icms_proprio = fields.Dinheiro('Base do ICMS próprio')
    al_icms_proprio = fields.Porcentagem('alíquota do ICMS próprio')
    vr_icms_proprio = fields.Dinheiro('valor do ICMS próprio')

    #
    # Parâmetros relativos ao ICMS Simples Nacional
    #
    cst_icms_sn = fields.Selection(ST_ICMS_SN, 'Situação tributária do ICMS - SIMPLES', index=True, default=ST_ICMS_SN_NAO_TRIBUTADA)
    al_icms_sn = fields.Porcentagem('Alíquota do crédito de ICMS')
    rd_icms_sn = fields.Porcentagem('% estadual de redução da alíquota de ICMS')
    vr_icms_sn = fields.Dinheiro('valor do crédito de ICMS - SIMPLES')
    al_simples = fields.Dinheiro('Alíquota do SIMPLES')
    vr_simples = fields.Dinheiro('Valor do SIMPLES')

    #
    # ICMS ST
    #
    md_icms_st = fields.Selection(MODALIDADE_BASE_ICMS_ST, 'Modalidade da base de cálculo do ICMS ST', default=MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO)
    pr_icms_st = fields.Quantidade('Parâmetro do ICMS ST')
    rd_icms_st = fields.Porcentagem('% de redução da base de cálculo do ICMS ST')
    bc_icms_st_com_ipi = fields.Boolean('IPI integra a base do ICMS ST?')
    bc_icms_st = fields.Dinheiro('Base do ICMS ST')
    al_icms_st = fields.Porcentagem('Alíquota do ICMS ST')
    vr_icms_st = fields.Dinheiro('Valor do ICMS ST')

    #
    # Parâmetros relativos ao ICMS retido anteriosvente por substituição tributária
    # na origem
    #
    md_icms_st_retido = fields.Selection(MODALIDADE_BASE_ICMS_ST, 'Modalidade da base de cálculo', default=MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO)
    pr_icms_st_retido = fields.Quantidade('Parâmetro da base de cáculo')
    rd_icms_st_retido = fields.Porcentagem('% de redução da base de cálculo do ICMS retido')
    bc_icms_st_retido = fields.Dinheiro('Base do ICMS ST retido na origem')
    al_icms_st_retido = fields.Porcentagem('Alíquota do ICMS ST retido na origem')
    vr_icms_st_retido = fields.Dinheiro('Valor do ICMS ST retido na origem')

    #
    # IPI padrão
    #
    apuracao_ipi = fields.Selection(APURACAO_IPI, 'Período de apuração do IPI', index=True, default=APURACAO_IPI_MENSAL)
    cst_ipi = fields.Selection(ST_IPI, 'Situação tributária do IPI', index=True, default=ST_IPI_SAIDA_NAO_TRIBUTADA)
    md_ipi = fields.Selection(MODALIDADE_BASE_IPI, 'Modalidade de cálculo do IPI', default=MODALIDADE_BASE_IPI_ALIQUOTA)
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
    al_pis_cofins_id = fields.Many2one('sped.aliquotapiscofins', 'Alíquota e CST do PIS-COFINS', index=True)
    cst_pis = fields.Selection(ST_PIS, 'Situação tributária do PIS', index=True, default=ST_PIS_SEM_INCIDENCIA)
    md_pis_proprio = fields.Selection(MODALIDADE_BASE_PIS, 'Modalidade de cálculo do PIS próprio', default=MODALIDADE_BASE_PIS_ALIQUOTA)
    bc_pis_proprio = fields.Dinheiro('Base do PIS próprio')
    al_pis_proprio = fields.Quantidade('Alíquota do PIS próprio')
    vr_pis_proprio = fields.Dinheiro('Valor do PIS próprio')

    #
    # COFINS própria
    #
    cst_cofins = fields.Selection(ST_COFINS, 'Situação tributária da COFINS', index=True, default=ST_COFINS_SEM_INCIDENCIA)
    md_cofins_proprio = fields.Selection(MODALIDADE_BASE_COFINS, 'Modalidade de cálculo da COFINS própria', default=MODALIDADE_BASE_COFINS_ALIQUOTA)
    bc_cofins_proprio = fields.Dinheiro('Base do COFINS próprio')
    al_cofins_proprio = fields.Quantidade('Alíquota da COFINS própria')
    vr_cofins_proprio = fields.Dinheiro('Valor do COFINS próprio')

    #
    # PIS ST
    #
    md_pis_st = fields.Selection(MODALIDADE_BASE_PIS, 'Modalidade de cálculo do PIS ST', default=MODALIDADE_BASE_PIS_ALIQUOTA)
    bc_pis_st = fields.Dinheiro('Base do PIS ST')
    al_pis_st = fields.Quantidade('Alíquota do PIS ST')
    vr_pis_st = fields.Dinheiro('Valor do PIS ST')

    #
    # COFINS ST
    #
    md_cofins_st = fields.Selection(MODALIDADE_BASE_COFINS, 'Modalidade de cálculo da COFINS ST', default=MODALIDADE_BASE_COFINS_ALIQUOTA)
    bc_cofins_st = fields.Dinheiro('Base do COFINS ST')
    al_cofins_st = fields.Quantidade('Alíquota da COFINS ST')
    vr_cofins_st = fields.Dinheiro('Valor do COFINS ST')

    #
    # Grupo ISS
    #

    # ISS
    cst_iss = fields.Selection(ST_ISS, 'Situação tributária do ISS', index=True)
    bc_iss = fields.Dinheiro('Base do ISS')
    al_iss = fields.Dinheiro('Alíquota do ISS')
    vr_iss = fields.Dinheiro('Valor do ISS')

    # PIS e COFINS
    vr_pis_servico = fields.Dinheiro('PIS sobre serviços')
    vr_cofins_servico = fields.Dinheiro('COFINS sobre serviços')

    #
    # Total da NF e da fatura (podem ser diferentes no caso de operação triangular)
    #
    vr_nf = fields.Dinheiro('Valor da NF', required=True)
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

    recalculo = fields.Integer('Campo para obrigar o recalculo dos itens')

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
    #quantidade_estoque = fields.function(_get_quantidade_estoque, type='float', string=u'Quantidade', store=False, digits=(18, 4))
    cfop_original_id = fields.Many2one('sped.cfop', 'CFOP original', index=True)

    credita_icms_proprio = fields.Boolean('Credita ICMS próprio?', index=True)
    credita_icms_st = fields.Boolean('Credita ICMS ST?', index=True)
    informa_icms_st = fields.Boolean('Informa ICMS ST?', index=True)
    credita_ipi = fields.Boolean('Credita IPI?', index=True)
    credita_pis_cofins = fields.Boolean('Credita PIS-COFINS?', index=True)

    ##
    ## Campos para rateio de custo
    ##
    #vr_frete_rateio = fields.function(_get_calcula_custo, type='float', string=u'Valor do frete', store=STORE_CUSTO, digits=(18, 2))
    #vr_seguro_rateio = fields.function(_get_calcula_custo, type='float', string=u'Valor do seguro', store=STORE_CUSTO, digits=(18, 2))
    #vr_outras_rateio = fields.function(_get_calcula_custo, type='float', string=u'Outras despesas acessórias', store=STORE_CUSTO, digits=(18, 2))
    #vr_desconto_rateio = fields.function(_get_calcula_custo, type='float', string=u'Valor do desconto', store=STORE_CUSTO, digits=(18, 2))
    #vr_unitario_custo = fields.function(_get_calcula_custo, type='float', string=u'Custo unitário', store=STORE_CUSTO, digits=(18, 4))
    #vr_custo = fields.function(_get_calcula_custo, type='float', string=u'Custo', store=STORE_CUSTO, digits=(18, 2))

    #
    # Parâmetros relativos ao ICMS ST compra
    # na origem
    #
    forca_recalculo_st_compra = fields.Boolean('Força recálculo do ST na compra?')
    md_icms_st_compra = fields.Selection(MODALIDADE_BASE_ICMS_ST, 'Modalidade da base de cálculo', default=MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO)
    pr_icms_st_compra = fields.Quantidade('Parâmetro da base de cáculo')
    rd_icms_st_compra = fields.Porcentagem('% de redução da base de cálculo do ICMS compra')
    bc_icms_st_compra = fields.Dinheiro('Base do ICMS ST compra')
    al_icms_st_compra = fields.Porcentagem('Alíquota do ICMS ST compra')
    vr_icms_st_compra = fields.Dinheiro('Valor do ICMS ST compra')

    #
    # Diferencial de alíquota
    #
    calcula_diferencial_aliquota = fields.Boolean('Calcula diferencial de alíquota?')
    al_diferencial_aliquota = fields.Porcentagem('Alíquota diferencial ICMS próprio')
    vr_diferencial_aliquota = fields.Dinheiro('Valor do diferencial de alíquota ICMS próprio')
    al_diferencial_aliquota_st = fields.Porcentagem('Alíquota diferencial ICMS ST')
    vr_diferencial_aliquota_st = fields.Dinheiro('Valor do diferencial de alíquota ICMS ST')
