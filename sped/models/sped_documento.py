# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

import logging
_logger = logging.getLogger(__name__)

try:
    from pybrasil.data import parse_datetime, data_hora_horario_brasilia
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
from ..constante_tributaria import *


class Documento(models.Model):
    _description = 'Documento Fiscal'
    _name = 'sped.documento'
    _order = 'emissao, modelo, data_emissao desc, serie, numero'
    _rec_name = 'numero'

    empresa_id = fields.Many2one('sped.empresa', 'Empresa', ondelete='restrict',
                                 default=lambda self: self.env['sped.empresa']._empresa_ativa('sped.documento'))
    empresa_cnpj_cpf = fields.Char('CNPJ/CPF', size=18, related='empresa_id.cnpj_cpf', readonly=True)
    emissao = fields.Selection(TIPO_EMISSAO, 'Tipo de emissão', index=True)
    modelo = fields.Selection(MODELO_FISCAL, 'Modelo', index=True)

    data_hora_emissao = fields.Datetime('Data de emissão', index=True, default=fields.Datetime.now)
    data_hora_entrada_saida = fields.Datetime('Data de entrada/saída', index=True, default=fields.Datetime.now)
    data_emissao = fields.Date('Data de emissão', compute='_compute_data_hora_separadas', store=True, index=True)
    hora_emissao = fields.Char('Hora de emissão', size=8, compute='_compute_data_hora_separadas', store=True)
    data_entrada_saida = fields.Date('Data de entrada/saída', compute='_compute_data_hora_separadas', store=True, index=True)
    hora_entrada_saida = fields.Char('Hora de entrada/saída', size=8, compute='_compute_data_hora_separadas', store=True)

    serie = fields.Char('Série', index=True)
    numero = fields.Float('Número', index=True, digits=(18, 0))
    entrada_saida = fields.Selection(ENTRADA_SAIDA, 'Entrada/Saída', index=True, default=ENTRADA_SAIDA_SAIDA)
    situacao_fiscal = fields.Selection(SITUACAO_FISCAL, 'Situação fiscal', index=True, default=SITUACAO_FISCAL_REGULAR)

    ambiente_nfe = fields.Selection(AMBIENTE_NFE, 'Ambiente da NF-e', index=True, default=AMBIENTE_NFE_HOMOLOGACAO)
    tipo_emissao_nfe = fields.Selection(TIPO_EMISSAO_NFE, 'Tipo de emissão da NF-e', default=TIPO_EMISSAO_NFE_NORMAL)
    ie_st = fields.Char('IE do substituto tributário', size=14)
    municipio_fato_gerador_id = fields.Many2one('sped.municipio', 'Município do fato gerador')

    operacao_id = fields.Many2one('sped.operacao', 'Operação', ondelete='restrict')
    #
    # Campos da operação
    #
    regime_tributario = fields.Selection(REGIME_TRIBUTARIO, 'Regime tributário', default=REGIME_TRIBUTARIO_SIMPLES)
    forma_pagamento = fields.Selection(FORMA_PAGAMENTO, 'Forma de pagamento', default=FORMA_PAGAMENTO_A_VISTA)
    finalidade_nfe = fields.Selection(FINALIDADE_NFE, 'Finalidade da NF-e', default=FINALIDADE_NFE_NORMAL)
    consumidor_final = fields.Selection(TIPO_CONSUMIDOR_FINAL, 'Tipo do consumidor',
                                        default=TIPO_CONSUMIDOR_FINAL_NORMAL)
    presenca_comprador = fields.Selection(INDICADOR_PRESENCA_COMPRADOR, 'Presença do comprador',
                                          default=INDICADOR_PRESENCA_COMPRADOR_NAO_SE_APLICA)
    modalidade_frete = fields.Selection(MODALIDADE_FRETE, 'Modalidade do frete', default=MODALIDADE_FRETE_DESTINATARIO_PROPRIO)
    natureza_operacao_id = fields.Many2one('sped.natureza.operacao', 'Natureza da operação', ondelete='restrict')
    infadfisco = fields.Text('Informações adicionais de interesse do fisco')
    infcomplementar = fields.Text('Informações complementares')
    deduz_retencao = fields.Boolean('Deduz retenção do total da NF?', default=True)
    pis_cofins_retido = fields.Boolean('PIS-COFINS retidos?')
    al_pis_retido = fields.Float('Alíquota do PIS', default=0.65, digits=(5, 2))
    al_cofins_retido = fields.Float('Alíquota da COFINS', default=3, digits=(5, 2))
    csll_retido = fields.Boolean('CSLL retido?')
    al_csll = fields.Float('Alíquota da CSLL', default=1, digits=(5, 2))

    #
    # Para todos os valores num documento fiscal, a moeda é SEMPRE o
    # Real BRL
    #
    currency_id = fields.Many2one('res.currency', 'Moeda', default=lambda self: self.env.ref('base.BRL').id)

    limite_retencao_pis_cofins_csll = fields.Monetary('Obedecer limite de faturamento para retenção de',
                                                      default=LIMITE_RETENCAO_PIS_COFINS_CSLL)
    irrf_retido = fields.Boolean('IR retido?')
    irrf_retido_ignora_limite = fields.Boolean('IR retido ignora limite de R$ 10,00?')
    al_irrf = fields.Float('Alíquota do IR', default=1, digits=(5, 2))
    inss_retido = fields.Boolean('INSS retido?', index=True)
    al_inss_retido = fields.Float('Alíquota do INSS', digits=(5, 2))
    al_inss = fields.Float(u'Alíquota do INSS', digits=(5, 2))
    cnae_id = fields.Many2one('sped.cnae', 'CNAE')
    natureza_tributacao_nfse = fields.Selection(NATUREZA_TRIBUTACAO_NFSE, 'Natureza da tributação')
    servico_id = fields.Many2one('sped.servico', 'Serviço')
    cst_iss = fields.Selection(ST_ISS, 'CST ISS')

    #
    # Destinatário/Remetente
    #
    participante_id = fields.Many2one('sped.participante', 'Destinatário/Remetente', ondelete='restrict')
    participante_cnpj_cpf = fields.Char('CNPJ/CPF', size=18, related='participante_id.cnpj_cpf', readonly=True)
    participante_tipo_pessoa = fields.Char('Tipo pessoa', size=1, related='participante_id.tipo_pessoa', readonly=True)
    participante_razao_social = fields.NameChar('Razão Social', size=60, related='participante_id.razao_social',
                                                readonly=True)
    participante_fantasia = fields.NameChar('Fantasia', size=60, related='participante_id.fantasia', readonly=True)
    participante_endereco = fields.NameChar('Endereço', size=60, related='participante_id.endereco', readonly=True)
    participante_numero = fields.Char('Número', size=60, related='participante_id.numero', readonly=True)
    participante_complemento = fields.Char('Complemento', size=60, related='participante_id.complemento', readonly=True)
    participante_bairro = fields.NameChar('Bairro', size=60, related='participante_id.bairro', readonly=True)
    participante_municipio_id = fields.Many2one('sped.municipio', string='Município',
                                                related='participante_id.municipio_id', readonly=True)
    participante_cidade = fields.NameChar('Município', related='participante_id.cidade', readonly=True)
    participante_estado = fields.UpperChar('Estado', related='participante_id.estado', readonly=True)
    participante_cep = fields.Char('CEP', size=9, related='participante_id.cep', readonly=True)
    #
    # Telefone e email para a emissão da NF-e
    #
    participante_fone = fields.Char('Fone', size=18, related='participante_id.fone', readonly=True)
    participante_fone_comercial = fields.Char('Fone Comercial', size=18, related='participante_id.fone_comercial',
                                              readonly=True)
    participante_celular = fields.Char('Celular', size=18, related='participante_id.celular', readonly=True)
    participante_email = fields.LowerChar('Email', size=60, related='participante_id.email', readonly=True)
    #
    # Inscrições e registros
    #
    participante_contribuinte = fields.Selection(IE_DESTINATARIO, string='Contribuinte', default='2',
                                                 related='participante_id.contribuinte', readonly=True)
    participante_ie = fields.Char('Inscrição estadual', size=18, related='participante_id.ie', readonly=True)

    #
    # Chave e validação da chave
    #
    chave = fields.Char('Chave', size=44)

    #
    # Transporte
    #
    transportadora_id = fields.Many2one('res.partner', 'Transportadora', ondelete='restrict',
                                        domain=[('cnpj_cpf', '!=', False)])
    veiculo_id = fields.Many2one('sped.veiculo', 'Veículo', ondelete='restrict')
    reboque_1_id = fields.Many2one('sped.veiculo', 'Reboque 1', ondelete='restrict')
    reboque_2_id = fields.Many2one('sped.veiculo', 'Reboque 2', ondelete='restrict')
    reboque_3_id = fields.Many2one('sped.veiculo', 'Reboque 3', ondelete='restrict')
    reboque_4_id = fields.Many2one('sped.veiculo', 'Reboque 4', ondelete='restrict')
    reboque_5_id = fields.Many2one('sped.veiculo', 'Reboque 5', ondelete='restrict')

    #
    # Totais dos itens
    #

    # Valor total dos produtos
    vr_produtos = fields.Monetary('Valor dos produtos/serviços', compute='_compute_soma_itens', store=True)
    vr_produtos_tributacao = fields.Monetary('Valor dos produtos para tributação', compute='_compute_soma_itens', store=True)
    vr_frete = fields.Monetary('Valor do frete', compute='_compute_soma_itens', store=True)
    vr_seguro = fields.Monetary('Valor do seguro', compute='_compute_soma_itens', store=True)
    vr_desconto = fields.Monetary('Valor do desconto', compute='_compute_soma_itens', store=True)
    vr_outras = fields.Monetary('Outras despesas acessórias', compute='_compute_soma_itens', store=True)
    vr_operacao = fields.Monetary('Valor da operação', compute='_compute_soma_itens', store=True)
    vr_operacao_tributacao = fields.Monetary('Valor da operação para tributação', compute='_compute_soma_itens', store=True)
    # ICMS próprio
    bc_icms_proprio = fields.Monetary('Base do ICMS próprio', compute='_compute_soma_itens', store=True)
    vr_icms_proprio = fields.Monetary('Valor do ICMS próprio', compute='_compute_soma_itens', store=True)
    # ICMS SIMPLES
    vr_icms_sn = fields.Monetary('Valor do crédito de ICMS - SIMPLES Nacional', compute='_compute_soma_itens', store=True)
    vr_simples = fields.Monetary('Valor do SIMPLES Nacional', compute='_compute_soma_itens', store=True)
    # ICMS ST
    bc_icms_st = fields.Monetary('Base do ICMS ST', compute='_compute_soma_itens', store=True)
    vr_icms_st = fields.Monetary('Valor do ICMS ST', compute='_compute_soma_itens', store=True)
    # ICMS ST retido
    bc_icms_st_retido = fields.Monetary('Base do ICMS retido anteriormente por substituição tributária', compute='_compute_soma_itens', store=True)
    vr_icms_st_retido = fields.Monetary('Valor do ICMS retido anteriormente por substituição tributária', compute='_compute_soma_itens', store=True)
    # IPI
    bc_ipi = fields.Monetary('Base do IPI', compute='_compute_soma_itens', store=True)
    vr_ipi = fields.Monetary('Valor do IPI', compute='_compute_soma_itens', store=True)
    # Imposto de importação
    bc_ii = fields.Monetary('Base do imposto de importação', compute='_compute_soma_itens', store=True)
    vr_despesas_aduaneiras = fields.Monetary('Despesas aduaneiras', compute='_compute_soma_itens', store=True)
    vr_ii = fields.Monetary('Valor do imposto de importação', compute='_compute_soma_itens', store=True)
    vr_iof = fields.Monetary('Valor do IOF', compute='_compute_soma_itens', store=True)
    # PIS e COFINS
    bc_pis_proprio = fields.Monetary('Base do PIS próprio', compute='_compute_soma_itens', store=True)
    vr_pis_proprio = fields.Monetary('Valor do PIS próprio', compute='_compute_soma_itens', store=True)
    bc_cofins_proprio = fields.Monetary('Base da COFINS própria', compute='_compute_soma_itens', store=True)
    vr_cofins_proprio = fields.Monetary('Valor do COFINS própria', compute='_compute_soma_itens', store=True)
    #bc_pis_st = fields.Monetary('Base do PIS ST', compute='_compute_soma_itens', store=True)
    #vr_pis_st = fields.Monetary('Valor do PIS ST', compute='_compute_soma_itens', store=True)
    #bc_cofins_st = fields.Monetary('Base da COFINS ST', compute='_compute_soma_itens', store=True)
    #vr_cofins_st = fields.Monetary('Valor do COFINS ST', compute='_compute_soma_itens', store=True)
    #
    # Totais dos itens (grupo ISS)
    #
    # ISS
    bc_iss = fields.Monetary('Base do ISS', compute='_compute_soma_itens', store=True)
    vr_iss = fields.Monetary('Valor do ISS', compute='_compute_soma_itens', store=True)
    # Total da NF e da fatura (podem ser diferentes no caso de operação triangular)
    vr_nf = fields.Monetary('Valor da NF', compute='_compute_soma_itens', store=True)
    vr_fatura = fields.Monetary('Valor da fatura', compute='_compute_soma_itens', store=True)
    vr_ibpt = fields.Monetary('Valor IBPT', compute='_compute_soma_itens', store=True)
    bc_inss_retido = fields.Monetary('Base do INSS', compute='_compute_soma_itens', store=True)
    vr_inss_retido = fields.Monetary('Valor do INSS', compute='_compute_soma_itens', store=True)
    vr_custo_comercial = fields.Monetary('Custo comercial', compute='_compute_soma_itens', store=True)
    vr_difal = fields.Monetary('Valor do diferencial de alíquota ICMS próprio', compute='_compute_soma_itens', store=True)
    vr_fcp = fields.Monetary('Valor do fundo de combate à pobreza', compute='_compute_soma_itens', store=True)

    ###
    ### Retenções de tributos (órgãos públicos, substitutos tributários etc.)
    ###
    ###'vr_operacao_pis_cofins_csll = CampoDinheiro(u'Base da retenção do PIS-COFINS e CSLL'),

    ### PIS e COFINS
    ##'pis_cofins_retido = fields.boolean(u'PIS-COFINS retidos?'),
    ##'al_pis_retido = CampoPorcentagem(u'Alíquota do PIS retido'),
    ##'vr_pis_retido = CampoDinheiro(u'PIS retido'),
    ##'al_cofins_retido = CampoPorcentagem(u'Alíquota da COFINS retida'),
    ##'vr_cofins_retido = CampoDinheiro(u'COFINS retida'),

    ### Contribuição social sobre lucro líquido
    ##'csll_retido = fields.boolean(u'CSLL retida?'),
    ##'al_csll = CampoPorcentagem('Alíquota da CSLL'),
    ##'vr_csll = CampoDinheiro(u'CSLL retida'),
    ##'bc_csll_propria = CampoDinheiro(u'Base da CSLL própria'),
    ##'al_csll_propria = CampoPorcentagem('Alíquota da CSLL própria'),
    ##'vr_csll_propria = CampoDinheiro(u'CSLL própria'),

    ### IRRF
    ##'irrf_retido = fields.boolean(u'IR retido?'),
    ##'bc_irrf = CampoDinheiro(u'Base do IRRF'),
    ##'al_irrf = CampoPorcentagem(u'Alíquota do IRRF'),
    ##'vr_irrf = CampoDinheiro(u'Valor do IRRF'),
    ##'bc_irpj_proprio = CampoDinheiro(u'Valor do IRPJ próprio'),
    ##'al_irpj_proprio = CampoPorcentagem(u'Alíquota do IRPJ próprio'),
    ##'vr_irpj_proprio = CampoDinheiro(u'Valor do IRPJ próprio'),

    ### ISS
    ##'iss_retido = fields.boolean(u'ISS retido?'),
    ##'bc_iss_retido = CampoDinheiro(u'Base do ISS'),
    ##'vr_iss_retido = CampoDinheiro(u'Valor do ISS'),

    item_ids = fields.One2many('sped.documento.item', 'documento_id', 'Itens')

    #
    # Outras informações
    #
    eh_compra = fields.Boolean('É compra?', compute='_compute_eh_compra_venda')
    eh_venda = fields.Boolean('É venda?', compute='_compute_eh_compra_venda')
    eh_devolucao_compra = fields.Boolean('É devolução de compra?', compute='_compute_eh_compra_venda')
    eh_devolucao_venda = fields.Boolean('É devolução de venda?', compute='_compute_eh_compra_venda')

    @api.depends('data_hora_emissao', 'data_hora_entrada_saida')
    def _compute_data_hora_separadas(self):
        for documento in self:
            data_hora_emissao = data_hora_horario_brasilia(parse_datetime(documento.data_hora_emissao))
            documento.data_emissao = str(data_hora_emissao)[:10]
            documento.hora_emissao = str(data_hora_emissao)[11:19]

            data_hora_entrada_saida = data_hora_horario_brasilia(parse_datetime(documento.data_hora_entrada_saida))
            documento.data_entrada_saida = str(data_hora_entrada_saida)[:10]
            documento.hora_entrada_saida = str(data_hora_entrada_saida)[11:19]

    #@api.depends(
            #'vr_produtos', 'vr_produtos_tributacao',
            #'vr_frete', 'vr_seguro', 'vr_desconto', 'vr_outras',
            #'vr_operacao', 'vr_operacao_tributacao',
            #'bc_icms_proprio', 'vr_icms_proprio',
            #'vr_difal', 'vr_fcp',
            #'vr_icms_sn', 'vr_simples',
            #'bc_icms_st', 'vr_icms_st',
            #'bc_icms_st_retido', 'vr_icms_st_retido',
            #'bc_ipi', 'vr_ipi',
            #'bc_ii', 'vr_ii', 'vr_despesas_aduaneiras', 'vr_iof',
            #'bc_pis_proprio', 'vr_pis_proprio',
            #'bc_cofins_proprio', 'vr_cofins_proprio',
            #'bc_iss', 'vr_iss',
            #'vr_nf', 'vr_fatura',
            #'vr_ibpt',
            #'bc_inss_retido', 'vr_inss_retido',
            #'vr_custo_comercial'
        #)
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

    #def _get_soma_funcao(self, cr, uid, ids, nome_campo, args, context=None):
        #res = {}

        #for doc_obj in self.browse(cr, uid, ids):
            #soma = D('0')
            #al_simples = D('0')

            #for item_obj in doc_obj.documentoitem_ids:
                ##
                ## Para o custo da mercadoria para baixa do custo na venda/devolução
                ##
                #if nome_campo == 'vr_custo_estoque':
                    #if item_obj.cfop_id.codigo in CFOPS_CUSTO_ESTOQUE_VENDA_DEVOLUCAO:
                        #soma += D(str(getattr(item_obj, nome_campo, 0)))

                ##
                ## Para o SIMPLES Nacional, somar o valor da operação
                ##
                #elif nome_campo == 'vr_simples':
                    #if D(str(getattr(item_obj, 'vr_simples', 0))):
                        #if al_simples == 0:
                            #al_simples = D(str(getattr(item_obj, 'al_simples', 0)))

                        #soma += D(str(getattr(item_obj, 'vr_operacao', 0)))
                #else:
                    #soma += D(str(getattr(item_obj, nome_campo, 0)))

            #soma = soma.quantize(D('0.01'))

            #if nome_campo == 'vr_fatura' and doc_obj.deduz_retencao:
                #soma -= D(str(doc_obj.vr_pis_retido))
                #soma -= D(str(doc_obj.vr_cofins_retido))
                #soma -= D(str(doc_obj.vr_csll))
                #soma -= D(str(doc_obj.vr_irrf))
                #soma -= D(str(doc_obj.vr_inss_retido))
                #soma -= D(str(doc_obj.vr_iss_retido))

            #if (nome_campo == 'bc_inss_retido' or nome_campo == 'vr_inss_retido') and doc_obj.deduz_retencao:
                #if soma < D('10'):
                    #soma = D('0')

            #if nome_campo == 'vr_simples' and soma > 0:
                #soma *= al_simples / D(100)
                #soma = soma.quantize(D('0.01'))

            #res[doc_obj.id] = soma

        #return res


    @api.onchange('empresa_id', 'modelo', 'emissao')
    def onchange_empresa_id(self):
        res = {}
        valores = {}
        res['value'] = valores

        if not self.empresa_id:
            return res

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        if self.modelo not in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE, MODELO_FISCAL_NFSE):
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
                    valores['serie'] = self.empresa_id.serie_nfe_contingencia_producao
                else:
                    valores['serie'] = self.empresa_id.serie_nfe_contingencia_homologacao

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
                    valores['serie'] = self.empresa_id.serie_nfce_contingencia_producao
                else:
                    valores['serie'] = self.empresa_id.serie_nfce_contingencia_homologacao

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
                valores['natureza_operacao_id'] = self.operacao_id.natureza_operacao_id.id

            if self.operacao_id.serie:
                valores['serie'] = self.operacao_id.serie

            valores['regime_tributario'] = self.operacao_id.regime_tributario
            valores['forma_pagamento'] = self.operacao_id.forma_pagamento
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
        valores['limite_retencao_pis_cofins_csll'] = self.operacao_id.limite_retencao_pis_cofins_csll
        valores['irrf_retido'] = self.operacao_id.irrf_retido
        valores['irrf_retido_ignora_limite'] = self.operacao_id.irrf_retido_ignora_limite
        valores['al_irrf'] = self.operacao_id.al_irrf
        valores['inss_retido'] = self.operacao_id.inss_retido
        valores['consumidor_final'] = self.operacao_id.consumidor_final
        valores['presenca_comprador'] = self.operacao_id.presenca_comprador

        if self.operacao_id.cnae_id:
            valores['cnae_id'] = self.operacao_id.cnae_id.id

        valores['natureza_tributacao_nfse'] = self.operacao_id.natureza_tributacao_nfse

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
        # Quando o tipo da nota for para consumidor normal, mas o participante não é
        # contribuinte, define que ele é consumidor final, exceto em caso de operação
        # com estrangeiros
        #
        if self.consumidor_final == TIPO_CONSUMIDOR_FINAL_NORMAL:
            if self.participante_id.estado != 'EX':
                if self.participante_id.contribuinte != INDICADOR_IE_DESTINATARIO:
                    valores['consumidor_final'] = TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL

        return res
