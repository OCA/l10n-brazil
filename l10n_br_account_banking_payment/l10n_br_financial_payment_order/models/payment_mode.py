# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models, _

from ..constantes import TIPO_SERVICO, FORMA_LANCAMENTO, \
    COMPLEMENTO_TIPO_SERVICO, CODIGO_FINALIDADE_TED, AVISO_FAVORECIDO, \
    CODIGO_INSTRUCAO_MOVIMENTO, TIPOS_ORDEM_PAGAMENTO, ORIGEM_PAGAMENTO, \
    BOLETO_ESPECIE

from ..febraban.boleto.document import getBoletoSelection

boleto_selection = getBoletoSelection()


class PaymentMode(models.Model):

    _inherit = b'payment.mode'

    boleto_carteira = fields.Char('Carteira', size=3)
    boleto_modalidade = fields.Char('Modalidade', size=2)
    boleto_convenio = fields.Char('Codigo convênio', size=10)
    boleto_variacao = fields.Char('Variação', size=2)
    boleto_cnab_code = fields.Char('Código Cnab', size=20)
    boleto_aceite = fields.Selection(
        [('S', 'Sim'), ('N', 'Não')], string='Aceite', default='N')

    boleto_type = fields.Selection(
        boleto_selection,
        string="Boleto"
    )

    boleto_especie = fields.Selection(
        string='Espécie do Título',
        selection=BOLETO_ESPECIE,
        default='01',
    )

    boleto_protesto = fields.Selection([
        ('0', 'Sem instrução'),
        ('1', 'Protestar (Dias Corridos)'),
        ('2', 'Protestar (Dias Úteis)'),
        ('3', 'Não protestar'),
        ('7', 'Negativar (Dias Corridos)'),
        ('8', 'Não Negativar')
    ], string='Códigos de Protesto', default='0')
    boleto_protesto_prazo = fields.Char('Prazo protesto', size=2)

    tipo_pagamento = fields.Selection(
        string="Tipos de Ordem de Pagamento",
        selection=TIPOS_ORDEM_PAGAMENTO,
        help="Tipos de Ordens de Pagamento.",
    )

    journal = fields.Many2one(
        required=False,
    )

    sale_ok = fields.Boolean(
        compute='_compute_sale_purchase_ok',
    )

    purchase_ok = fields.Boolean(
        compute='_compute_sale_purchase_ok',
    )

    tipo_servico = fields.Selection(
        selection=TIPO_SERVICO,
        string=u'Tipo de Serviço',
        help=u'Campo G025 do CNAB'
    )

    origem_pagamento = fields.Selection(
        selection=ORIGEM_PAGAMENTO,
        string=u'Origem do pagamento',
    )

    forma_lancamento = fields.Selection(
        selection=FORMA_LANCAMENTO,
        string=u'Forma Lançamento',
        help=u'Campo G029 do CNAB'
    )

    codigo_convenio = fields.Char(
        size=20,
        string=u'Código do Convênio no Banco',
        help=u'Campo G007 do CNAB',
        default=u'0001222130126',
    )

    codigo_instrucao_movimento = fields.Selection(
        selection=CODIGO_INSTRUCAO_MOVIMENTO,
        string='Código da Instrução para Movimento',
        help='Campo G061 do CNAB',
        default='0',
    )

    aviso_ao_favorecido = fields.Selection(
        selection=AVISO_FAVORECIDO,
        string='Aviso ao Favorecido',
        help='Campo P006 do CNAB',
        default=0,
    )

    sufixo_arquivo = fields.Integer(
        string=u'Sufixo do arquivo',
    )

    sequencia_arquivo = fields.Many2one(
        comodel_name='ir.sequence',
        string=u'Sequência para arquivos do CNAB',
    )

    proximo_sequencia_arquivo = fields.Integer(
        related='sequencia_arquivo.number_next_actual',
        string='Próximo valor Sequencia do arquivo',
    )

    sequencia_nosso_numero = fields.Many2one(
        comodel_name='ir.sequence',
        string=u'Sequência (Numero do banco)',
    )

    proximo_sequencia_nosso_numero = fields.Integer(
        string='Próximo Valor Sequencia nosso Número',
        related='sequencia_nosso_numero.number_next_actual',
    )

    codigo_finalidade_doc = fields.Selection(
        selection=COMPLEMENTO_TIPO_SERVICO,
        string='Complemento do Tipo de Serviço',
        help='Campo P005 do CNAB'
    )

    codigo_finalidade_ted = fields.Selection(
        selection=CODIGO_FINALIDADE_TED,
        string='Código Finalidade da TED',
        help='Campo P011 do CNAB'
    )

    codigo_finalidade_complementar = fields.Char(
        size=2,
        string='Código de finalidade complementar',
        help='Campo P013 do CNAB',
    )

    @api.multi
    @api.depends('tipo_servico')
    def _compute_sale_purchase_ok(self):
        for record in self:
            if record.tipo_servico in ['01']:
                record.sale_ok = True
            elif record.tipo_servico in ['03']:
                record.purchase_ok = True
