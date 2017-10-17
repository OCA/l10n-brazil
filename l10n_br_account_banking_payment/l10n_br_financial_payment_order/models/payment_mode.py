# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models, _

# from ..constantes import TIPO_SERVICO, FORMA_LANCAMENTO, \
#     TIPO_SERVICO_COMPLEMENTO, CODIGO_FINALIDADE_TED, AVISO_FAVORECIDO, \
#     INSTRUCAO_MOVIMENTO, TIPO_ORDEM_PAGAMENTO, \
#     BOLETO_ESPECIE, BOLETO_ESPECIE_DUPLICATA_MERCANTIL, \
#     BOLETO_EMISSAO, BOLETO_EMISSAO_BENEFICIARIO, \
#     BOLETO_ENTREGA, BOLETO_ENTREGA_BENEFICIARIO
from ..constantes import *


class PaymentMode(models.Model):
    '''
    O objetivo deste model é gerenciar as interações do módulo
    financeiro com o sistema bancário brasileiro, no que toca 
    a troca dos chamados arquivos padrão CNAB, tratando de 
    arquivos de cobrança (vindos do contas a receber, os boletos),
    e várias modalidades de pagamento (vindos do contas a pagar)
    '''
    _inherit = b'payment.mode'
    
    #
    # Primeiro, removemos o vínculo fixo da classe com o módulo original 
    # account
    #
    journal = fields.Many2one(
        required=False,
    )
    
    #
    # Campos comuns a todas ou pelo menos a maioria dos tipos de arquivo
    #
    tipo_pagamento = fields.Selection(
        string='Tipos da ordem de pagamento',
        selection=TIPO_ORDEM_PAGAMENTO,
        help='Tipos de Ordens de Pagamento.',
    )
    tipo_servico = fields.Selection(
        selection=TIPO_SERVICO,
        string='Tipo de serviço',
        help='Campo G025 do CNAB'
    )
    tipo_servico_complemento = fields.Selection(
        selection=TIPO_SERVICO_COMPLEMENTO,
        string='Complemento do tipo de serviço',
        help='Campo P005 do CNAB'
    )
    forma_lancamento = fields.Selection(
        selection=FORMA_LANCAMENTO,
        string='Forma de lançamento',
        help='Campo G029 do CNAB'
    )
    convenio = fields.Char(
        string='Convênio',
        size=20,
        help='Campo G007 do CNAB',
    )
    beneficiario_codigo = fields.Char(
        string='Código do beneficiário',
        size=20,
    )
    beneficiario_digito = fields.Char(
        string='Dígito do beneficiário',
        size=1,
    )
    instrucao_movimento = fields.Selection(
        selection=INSTRUCAO_MOVIMENTO,
        string='Instrução para Movimento',
        help='Campo G061 do CNAB',
        default=INSTRUCAO_MOVIMENTO_INCLUSAO_DETALHE_LIBERADO,
    )
    aviso_favorecido = fields.Selection(
        selection=AVISO_FAVORECIDO,
        string='Aviso ao favorecido',
        help='Campo P006 do CNAB',
        default=0,
    )
    finalidade_ted = fields.Selection(
        selection=CODIGO_FINALIDADE_TED,
        string='Finalidade da TED',
        help='Campo P011 do CNAB'
    )
    finalidade_complementar = fields.Char(
        string='Finalidade complementar',
        size=2,
        help='Campo P013 do CNAB',
    )

    #
    # Controle dos arquivos e nossos números
    #
    sufixo_arquivo = fields.Integer(
        string='Sufixo do arquivo',
    )
    sequence_arquivo_id = fields.Many2one(
        comodel_name='ir.sequence',
        string='Sequência do arquivo',
    )
    sequence_arquivo_proximo_numero = fields.Integer(
        related='sequence_arquivo_id.number_next_actual',
        string='Próximo número do arquivo',
    )
    sequence_nosso_numero_id = fields.Many2one(
        comodel_name='ir.sequence',
        string='Sequência do Nosso Número',
    )
    sequence_nosso_numero_proximo_numero = fields.Integer(
        string='Próximo nosso número',
        related='sequence_nosso_numero_id.number_next_actual',
    )

    #
    # Campos antigos que agora são calculados
    #
    sale_ok = fields.Boolean(
        compute='_compute_sale_purchase_ok',
    )
    purchase_ok = fields.Boolean(
        compute='_compute_sale_purchase_ok',
    )

    #
    # Configurações para emissão de boleto
    #
    boleto_carteira = fields.Char(
        string='Carteira', 
        size=10,
    )
    boleto_modalidade = fields.Char(
        string='Modalidade', 
        size=3,
    )
    boleto_variacao = fields.Char(
        string='Variação', 
        size=3,
    )
    boleto_codigo_cnab = fields.Char(
        string='Código Cnab', 
        size=20,
    )
    # boleto_protesto = fields.Selection([
    #     ('0', 'Sem instrução'),
    #     ('1', 'Protestar (Dias Corridos)'),
    #     ('2', 'Protestar (Dias Úteis)'),
    #     ('3', 'Não protestar'),
    #     ('7', 'Negativar (Dias Corridos)'),
    #     ('8', 'Não Negativar')
    # ], string='Códigos de Protesto', default='0')
    boleto_dias_protesto = fields.Integer(
        string='Dias para protesto',
    )
    boleto_aceite = fields.Selection(
        string='Aceite',
        selection=[('S', 'Sim'), ('N', 'Não')],
        default='N',
    )
    boleto_especie = fields.Selection(
        string='Espécie do Título',
        selection=BOLETO_ESPECIE,
        default=BOLETO_ESPECIE_DUPLICATA_MERCANTIL,
    )
    boleto_emissao = fields.Selection(
        selection=BOLETO_EMISSAO,
        string='Emissão',
        default=BOLETO_EMISSAO_BENEFICIARIO,
    )
    boleto_entrega = fields.Selection(
        selection=BOLETO_DISTRIBUICAO,
        string='Entrega',
        default=BOLETO_DISTRIBUICAO_BENEFICIARIO,
    )

    #
    # Controles para os lançamentos financeiros das remessas e retornos
    #
    gera_financeiro_remessa = fields.Boolean(
        string='Gerar lançamento financeiro ao processar a remessa',
    )
    remessa_financial_account_id = fields.Many2one(
        comodel_name='financial.account',
        string='Conta financeira',
        domain=[('type', '=', 'A')],
    )
    remessa_document_type_id = fields.Many2one(
        comodel_name='financial.document.type',
        string='Tipo de documento',
    )
    gera_financeiro_retorno = fields.Boolean(
        string='Gerar lançamento financeiro ao processar o retorno',
    )
    retorno_financial_account_id = fields.Many2one(
        comodel_name='financial.account',
        string='Conta financeira',
        domain=[('type', '=', 'A')],
    )
    retorno_document_type_id = fields.Many2one(
        comodel_name='financial.document.type',
        string='Tipo de documento',
    )


    #
    # Controle de aprovação das ordens de pagamento/arquivos CNAB
    #
    nivel_aprovacao = fields.Selection(
        selection=[
            ('0', 'Nenhuma / Aprovar e gerar o arquivo'),
            ('1', 'Uma aprovação'),
            ('2', 'Duas aprovações'),
        ],
        required=True,
        default='0',
    )
    aprovacao_grupo_1 = fields.Many2one(
        comodel_name='res.groups',
        string='Grupo primeira aprovação'
    )
    aprovacao_grupo_2 = fields.Many2one(
        comodel_name='res.groups',
        string='Grupo segunda aprovação'
    )

    @api.depends('tipo_servico')
    def _compute_sale_purchase_ok(self):
        for payment_mode in self:
            if payment_mode.tipo_servico in ['01']:
                payment_mode.sale_ok = True
            elif payment_mode.tipo_servico in ['03']:
                payment_mode.purchase_ok = True

    @api.depends('tipo_servico')
    def _onchange_tipo_servico(self):
        for payment_mode in self:
            if payment_mode.tipo_servico == TIPO_SERVICO_PAGAMENTO_FORNECEDOR:
                payment_mode.tipo_servico_complemento = \
                    TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_FORNECEDORES

            elif payment_mode.tipo_servico == TIPO_SERVICO_PAGAMENTO_SALARIOS:
                payment_mode.tipo_servico_complemento = \
                    TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_SALARIOS

            elif payment_mode.tipo_servico == \
                    TIPO_SERVICO_PAGAMENTO_HONORARIOS:
                payment_mode.tipo_servico_complemento = \
                    TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_HONORARIOS

            elif payment_mode.tipo_servico == \
                    TIPO_SERVICO_PAGAMENTO_BOLSA_AUXILIO:
                payment_mode.tipo_servico_complemento = \
                    TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_BOLSA_AUXILIO

            elif payment_mode.tipo_servico == \
                    TIPO_SERVICO_PAGAMENTO_REMUNERACAO:
                payment_mode.tipo_servico_complemento = \
                    TIPO_SERVICO_COMPLEMENTO_REMUNERACAO_COOPERADO

            elif payment_mode.tipo_servico == \
                    TIPO_SERVICO_PAGAMENTO_PREBENDA:
                payment_mode.tipo_servico_complemento = \
                    TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_PREBENDA
