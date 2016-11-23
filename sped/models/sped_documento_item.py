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
    regime_tributario = fields.Selection(REGIME_TRIBUTARIO, 'Regime tributário', related='documento_id.regime_tributario', readonly=True)
    modelo = fields.Selection(MODELO_FISCAL, 'Modelo', related='documento_id.modelo', readonly=True)
    empresa_id = fields.Many2one('sped.empresa', 'Empresa', related='documento_id.empresa_id', readonly=True)
    participante_id = fields.Many2one('sped.participante', 'Destinatário/Remetente', related='documento_id.participante_id', readonly=True)
    operacao_id = fields.Many2one('sped.operacao', 'Operação Fiscal', related='documento_id.operacao_id', readonly=True)
    contribuinte = fields.Selection(IE_DESTINATARIO, string='Contribuinte', related='participante_id.contribuinte', readonly=True)
    emissao = fields.Selection(TIPO_EMISSAO, 'Tipo de emissão', related='documento_id.emissao', readonly=True)
    entrada_saida = fields.Selection(ENTRADA_SAIDA, 'Entrada/saída', related='documento_id.entrada_saida', readonly=True)
    consumidor_final = fields.Selection(TIPO_CONSUMIDOR_FINAL, 'Tipo do consumidor', related='documento_id.consumidor_final', readonly=True)

    #empresa_id = fields.Many2one('res.empresa', 'Empresa', ondelete='restrict', related='documento_id.empresa_id')
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
    cfop_posicao = fields.Selection(POSICAO_CFOP, 'Posição da CFOP', related='cfop_id.posicao', readonly=True)
    cfop_eh_venda = fields.Boolean('CFOP é venda?', related='cfop_id.eh_venda', readonly=True)
    compoe_total = fields.Boolean('Compõe o valor total da NF-e?', index=True, default=True)
    movimentacao_fisica = fields.Boolean('Há movimentação física do produto?', default=True)

    # Dados do produto/serviço
    #produto_id = fields.Many2one('produto.produto', 'Produto/Serviço', ondelete='restrict', index=True)
    #uom_id = fields.related('produto_id', 'uom_id', type='Many2one', relation='produto.uom', string=u'Unidade', index=True)
    produto_id = fields.Many2one('sped.produto', 'Produto/Serviço', ondelete='restrict', index=True)
    unidade_id = fields.Many2one('sped.unidade', 'Unidade', related='produto_id.unidade_id', readonly=True)

    protocolo_id = fields.Many2one('sped.protocolo.icms', 'Protocolo ICMS', ondelete='restrict')
    operacao_item_id = fields.Many2one('sped.operacao.item', 'Item da operação fiscal', ondelete='restrict')

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
    #contribuinte = fields.related('participante_id', 'contribuinte', type='char', string=u'Contribuinte', store=False, index=True)
    org_icms = fields.Selection(ORIGEM_MERCADORIA, 'Origem da mercadoria', index=True, default=ORIGEM_MERCADORIA_NACIONAL)
    cst_icms = fields.Selection(ST_ICMS, 'CST ICMS', index=True, default=ST_ICMS_ISENTA)
    partilha = fields.Boolean('Partilha de ICMS entre estados (CST 10 ou 90)?')
    al_bc_icms_proprio_partilha = fields.Porcentagem('% da base de cálculo da operação própria')
    estado_partilha_id = fields.Many2one('sped.estado', 'Estado para o qual é devido o ICMS ST', index=True)
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
    cst_icms_sn = fields.Selection(ST_ICMS_SN, 'CST ICMS - SIMPLES', index=True, default=ST_ICMS_SN_NAO_TRIBUTADA)
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
    # Parâmetros relativos ao ICMS retido anteriormente por substituição tributária
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
    cst_ipi = fields.Selection(ST_IPI, 'CST IPI', index=True)
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
    md_pis_proprio = fields.Selection(MODALIDADE_BASE_PIS, 'Modalidade BC do PIS próprio', default=MODALIDADE_BASE_PIS_ALIQUOTA)
    bc_pis_proprio = fields.Dinheiro('Base do PIS próprio')
    al_pis_proprio = fields.Quantidade('Alíquota do PIS próprio')
    vr_pis_proprio = fields.Dinheiro('Valor do PIS próprio')

    #
    # COFINS própria
    #
    cst_cofins = fields.Selection(ST_COFINS, 'CST COFINS', index=True)
    md_cofins_proprio = fields.Selection(MODALIDADE_BASE_COFINS, 'Modalidade BC da COFINS própria', default=MODALIDADE_BASE_COFINS_ALIQUOTA)
    bc_cofins_proprio = fields.Dinheiro('Base do COFINS próprio')
    al_cofins_proprio = fields.Quantidade('Alíquota da COFINS própria')
    vr_cofins_proprio = fields.Dinheiro('Valor do COFINS próprio')

    ##
    ## PIS ST
    ##
    #md_pis_st = fields.Selection(MODALIDADE_BASE_PIS, 'Modalidade BC do PIS ST', default=MODALIDADE_BASE_PIS_ALIQUOTA)
    #bc_pis_st = fields.Dinheiro('Base do PIS ST')
    #al_pis_st = fields.Quantidade('Alíquota do PIS ST')
    #vr_pis_st = fields.Dinheiro('Valor do PIS ST')

    ##
    ## COFINS ST
    ##
    #md_cofins_st = fields.Selection(MODALIDADE_BASE_COFINS, 'Modalidade BC da COFINS ST', default=MODALIDADE_BASE_COFINS_ALIQUOTA)
    #bc_cofins_st = fields.Dinheiro('Base do COFINS ST')
    #al_cofins_st = fields.Quantidade('Alíquota da COFINS ST')
    #vr_cofins_st = fields.Dinheiro('Valor do COFINS ST')

    #
    # Grupo ISS
    #

    # ISS
    #cst_iss = fields.Selection(ST_ISS, 'CST ISS', index=True)
    bc_iss = fields.Dinheiro('Base do ISS')
    al_iss = fields.Dinheiro('Alíquota do ISS')
    vr_iss = fields.Dinheiro('Valor do ISS')

    ## PIS e COFINS
    #vr_pis_servico = fields.Dinheiro('PIS sobre serviços')
    #vr_cofins_servico = fields.Dinheiro('COFINS sobre serviços')

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

    ##
    ## Campos readonly
    ##
    #@api.one
    #@api.depends('cst_pis', 'cst_cofins', 'al_pis_proprio', 'al_cofins_proprio', 'md_pis_proprio', 'md_cofins_proprio')
    #def _readonly(self):
        #self.cst_pis_readonly = self.cst_pis
        #self.cst_cofins_readonly = self.cst_cofins
        #self.md_pis_proprio_readonly = self.md_pis_proprio
        #self.md_cofins_proprio_readonly = self.md_cofins_proprio
        #self.al_pis_proprio_readonly = self.al_pis_proprio
        #self.al_cofins_proprio_readonly = self.al_cofins_proprio
        #print('passou readonly', self.cst_pis, self.cst_cofins, self.al_pis_proprio, self.al_cofins_proprio, self.md_pis_proprio, self.md_cofins_proprio)
        #print('passou readonly', self.cst_pis_readonly, self.cst_cofins_readonly, self.al_pis_proprio_readonly, self.al_cofins_proprio_readonly, self.md_pis_proprio_readonly, self.md_cofins_proprio_readonly)

    #cst_pis_readonly = fields.Selection(ST_PIS, 'CST PIS', compute=_readonly)
    #md_pis_proprio_readonly = fields.Selection(MODALIDADE_BASE_PIS, 'Modalidade BC do PIS próprio', compute=_readonly)
    #al_pis_proprio_readonly = fields.Quantidade('Alíquota do PIS próprio', compute=_readonly)

    #cst_cofins_readonly = fields.Selection(ST_COFINS, 'CST COFINS', compute=_readonly)
    #md_cofins_proprio_readonly = fields.Selection(MODALIDADE_BASE_COFINS, 'Modalidade BC da COFINS própria', compute=_readonly)
    #al_cofins_proprio_readonly = fields.Quantidade('Alíquota da COFINS própria', compute=_readonly)

    @api.depends('produto_descricao')
    @api.onchange('produto_id')
    def onchange_produto_id(self):
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

        #
        # Determinamos as UFs de origem e destino
        #
        if self.entrada_saida == ENTRADA_SAIDA_SAIDA:
            estado_origem = self.empresa_id.estado
            estado_destino = self.participante_id.estado

        else:
            estado_origem = self.participante_id.estado
            estado_destino = self.empresa_id.estado

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

        elif self.produto_id.ncm_id and self.produto_id.ncm_id.protocolo_ids:
            if len(self.produto_id.ncm_id.protocolo_ids):
                protocolo = self.produto_id.ncm_id.protocolo_ids[0]

            else:
                busca_protocolo = [
                    ('id', 'in', self.produto_id.ncm_id.protocolo_ids),
                    '|',
                    ('estado_ids', '=', False),
                    ('estado_ids.uf', '=', estado_destino)
                ]
                protocolo_ids = self.env['sped.protocolo.icms'].search(busca_protocolo)
                print('protocolo_ids', protocolo_ids)

        elif self.empresa_id.protocolo_id:
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
                    mensagem_erro = 'Não há protocolo padrão para a empresa, e o protocolo “{protocolo}” não pode ser usado para o estado “{estado}” (produto “{produto}”, NCM “{ncm}”)!'.format(protocolo=protocolo.descricao, estado=estado_destino, produto=self.produto_id.nome, ncm=self.produto_id.ncm_id.codigo_formatado)
                else:
                    mensagem_erro = 'Não há protocolo padrão para a empresa, e o protocolo “{protocolo}” não pode ser usado para o estado “{estado}” (produto “{produto}”)!'.format(protocolo=protocolo.descricao, estado=estado_destino, produto=self.produto_id.nome)

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
        # Se não houver um item da operação vinculado ao protocolo, tentamos
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
        # buscamos então o item genérico, sem protocolo
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
                mensagem_erro = 'Não há nenhum item genério na operação, nem específico para o protocolo “{protocolo}”, configurado para operações {estado}!'
            else:
                mensagem_erro = 'Há mais de um item genério na operação, ou mais de um item específico para o protocolo “{protocolo}”, configurado para operações {estado}!'

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

        valores['protocolo_id'] = protocolo.id
        valores['operacao_item_id'] = operacao_item.id

        return res

    @api.depends('emissao', 'modelo')
    @api.onchange('regime_tributario')
    def onchange_regime_tributario(self):
        res = {}
        valores = {}
        res['value'] = valores

        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            #
            # Força a CST do PIS, COFINS e IPI para o SIMPLES
            #
            valores['cst_ipi'] = ''  # NF-e do SIMPLES não destaca IPI nunca
            al_pis_cofins = self.env.ref('sped.ALIQUOTA_PIS_COFINS_SIMPLES')
            valores['al_pis_cofins_id'] = al_pis_cofins.id

        else:
            #
            # A nota não é do SIMPLES, zera o SIMPLES e o crédito de ICMS
            #
            valores['al_simples'] = 0
            valores['al_icms_sn'] = 0

        return res

    #@api.depends()
    @api.onchange('protocolo_id')
    def onchange_protocolo_id(self):
        pass

    @api.depends('produto_id', 'empresa_id', 'regime_tributario')
    @api.onchange('operacao_item_id')
    def onchange_operacao_item_id(self):
        res = {}
        valores = {}
        res['value'] = valores

        if not self.operacao_item_id:
            return res

        valores['cfop_id'] = self.operacao_item_id.cfop_id.id
        valores['compoe_total'] = self.operacao_item_id.compoe_total
        valores['movimentacao_fisica'] = self.operacao_item_id.movimentacao_fisica
        valores['bc_icms_proprio_com_ipi'] = self.operacao_item_id.bc_icms_proprio_com_ipi
        valores['bc_icms_st_com_ipi'] = self.operacao_item_id.bc_icms_st_com_ipi
        valores['cst_icms'] = self.operacao_item_id.cst_icms
        valores['cst_icms_sn'] = self.operacao_item_id.cst_icms_sn
        valores['cst_ipi'] = self.operacao_item_id.cst_ipi

        #
        # Busca agora as alíquotas do PIS e COFINS
        #
        if self.regime_tributario != REGIME_TRIBUTARIO_SIMPLES:
            #
            # Determina a alíquota do PIS-COFINS:
            # 1º - se o produto tem uma específica
            # 2º - se o NCM tem uma específica
            # 3º - a geral da empresa
            #
            if self.produto_id.al_pis_cofins_id:
                al_pis_cofins = self.produto_id.al_pis_cofins_id
            #elif self.produto_id.ncm_id.al_pis_cofins_id:
                #al_pis_cofins = self.produto_id.ncm_id.al_pis_cofins_id
            else:
                al_pis_cofins = self.empresa_id.al_pis_cofins_id

            #
            # Se por acaso a CST do PIS-COFINS especificada no item da operação
            # definir que não haverá cobrança de PIS-COFINS, usa a CST da operação
            # caso contrário, usa a definida acima
            #
            if self.operacao_item_id.al_pis_cofins_id and \
                not (self.operacao_item_id.al_pis_cofins_id.cst_pis_cofins_saida in ST_PIS_CALCULA_ALIQUOTA \
                or self.operacao_item_id.al_pis_cofins_id.cst_pis_cofins_saida in ST_PIS_CALCULA_QUANTIDADE):
                al_pis_cofins = self.operacao_item_id.al_pis_cofins_id

            valores['al_pis_cofins_id'] = al_pis_cofins.id

        return res

    @api.depends('regime_tributario', 'consumidor_final')
    @api.onchange('cfop_id')
    def onchange_cfop_id(self):
        res = {}
        valores = {}
        res['value'] = valores

        if not self.cfop_id:
            return res

        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            if self.cfop_id.calcula_simples_csll_irpj:
                valores['al_simples'] = self.empresa_id.simples_aliquota_id.al_simples

            else:
                valores['al_simples'] = 0

            valores['calcula_diferencial_aliquota'] = False

        else:
            valores['al_simples'] = 0
            valores['al_icms_sn'] = 0

            if self.consumidor_final == TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL and self.cfop_id.eh_venda:
                valores['calcula_diferencial_aliquota'] = True

        return res

    @api.depends('emissao', 'modelo', 'entrada_saida')
    @api.onchange('al_pis_cofins_id')
    def onchange_al_pis_cofins_id(self):
        res = {}
        valores = {}
        res['value'] = valores

        if (self.emissao != TIPO_EMISSAO_PROPRIA):
            if (self.modelo in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE)):
                return res

        if not self.al_pis_cofins_id:
            return res

        valores['md_pis_proprio'] = self.al_pis_cofins_id.md_pis_cofins
        valores['al_pis_proprio'] = self.al_pis_cofins_id.al_pis or 0

        valores['md_cofins_proprio'] = self.al_pis_cofins_id.md_pis_cofins
        valores['al_cofins_proprio'] = self.al_pis_cofins_id.al_cofins or 0

        if self.entrada_saida == ENTRADA_SAIDA_ENTRADA:
            valores['cst_pis'] = self.al_pis_cofins_id.cst_pis_cofins_entrada
            valores['cst_cofins'] = self.al_pis_cofins_id.cst_pis_cofins_entrada
        else:
            valores['cst_pis'] = self.al_pis_cofins_id.cst_pis_cofins_saida
            valores['cst_cofins'] = self.al_pis_cofins_id.cst_pis_cofins_saida

        return res

    @api.depends('emissao', 'modelo', 'entrada_saida', 'operacao_item_id', 'produto_id')
    @api.onchange('cst_ipi')
    def onchange_cst_ipi(self):
        res = {}
        valores = {}
        res['value'] = valores

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            if self.cst_ipi:
                raise ValidationError('Para o regime tributário do SIMPLES não há destaque de IPI!')

        else:
            if not self.cst_ipi:
                valores['bc_ipi'] = 0
                valores['al_ipi'] = 0
                valores['vr_ipi'] = 0
                valores['bc_icms_proprio_com_ipi'] = False
                valores['bc_icms_st_com_ipi'] = False
                return res

            print('self.cst_ipi, entrada_saida')
            print(self.cst_ipi, self.entrada_saida, self.cst_ipi in ST_IPI_SAIDA_DICT)

            if self.entrada_saida == ENTRADA_SAIDA_ENTRADA and self.cst_ipi not in ST_IPI_ENTRADA_DICT:
                raise ValidationError('Selecione um código de situação tributária de entrada!')

            elif self.entrada_saida == ENTRADA_SAIDA_SAIDA and self.cst_ipi not in ST_IPI_SAIDA_DICT:
                raise ValidationError('Selecione um código de situação tributária de saída!')

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
            valores['bc_ipi'] = 0
            valores['al_ipi'] = 0
            valores['vr_ipi'] = 0
            valores['bc_icms_proprio_com_ipi'] = False
            valores['bc_icms_st_com_ipi'] = False

        else:
            valores['md_ipi'] = al_ipi.md_ipi
            valores['al_ipi'] = al_ipi.al_ipi
            valores['bc_icms_proprio_com_ipi'] = self.operacao_item_id.bc_icms_proprio_com_ipi
            valores['bc_icms_st_com_ipi'] = self.operacao_item_id.bc_icms_st_com_ipi

        return res

    @api.depends('empresa_id', 'emissao', 'cfop_id')
    @api.onchange('cst_icms_sn')
    def onchange_cst_icms_sn(self):
        res = {}
        valores = {}
        res['value'] = valores

        if self.emissao != TIPO_EMISSAO_PROPRIA or not self.cst_icms_sn:
            return res

        if self.cst_icms_sn in ST_ICMS_SN_CALCULA_CREDITO:
            if not (self.cfop_id.eh_venda_industrializacao or self.cfop_id.eh_venda_comercializacao):
                raise ValidationError('Você selecionou uma CSOSN que dá direito a crédito, porém a CFOP não indica uma venda!')

            valores['al_icms_sn'] = self.empresa_id.simples_aliquota_id.al_icms
        else:
            valores['al_icms_sn'] = 0

        return res

    @api.depends('protocolo_id', 'emissao', 'cfop_id', 'empresa_id', 'participante_id', 'entrada_saida')
    @api.onchange('cst_icms')
    def onchange_cst_icms(self):
        res = {}
        valores = {}
        res['value'] = valores

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        if not self.cst_icms:
            return res

        if not (self.cst_icms in ST_ICMS_CALCULA_PROPRIO or self.cst_icms in ST_ICMS_CALCULA_ST):
            valores['md_icms_proprio'] = MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO
            valores['pr_icms_proprio'] = 0
            valores['rd_icms_proprio'] = 0
            valores['bc_icms_proprio'] = 0
            valores['al_icms_proprio'] = 0
            valores['vr_icms_proprio'] = 0
            valores['al_diferencial_aliquota'] = 0
            valores['vr_diferencial_aliquota'] = 0

            valores['md_icms_st'] = MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO
            valores['pr_icms_st'] = 0
            valores['rd_icms_st'] = 0
            valores['bc_icms_st'] = 0
            valores['al_icms_st'] = 0
            valores['vr_icms_st'] = 0
            valores['al_diferencial_aliquota_st'] = 0
            valores['vr_diferencial_aliquota_st'] = 0

        return res
