# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FinanceiroCheque(models.Model):

    _name = b'financeiro.cheque'
    _description = 'Cadastrar Cheques'

    name = fields.Char()

    financial_move_ids = fields.Many2many(
        comodel_name='financial.move',
        string=u'Movimentações'
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        ondelete='set null',
        index=True,
    )
    codigo = fields.Char(
        string=u'Código de Barras'
    )
    banco_id = fields.Many2one(
        comodel_name='res.bank',
        string=u'Banco'
    )
    agencia = fields.Many2one(
        string=u'Agência',
        comodel_name='res.bank.agencia'
    )
    conta = fields.Char(
        string=u'Conta Corrente'
    )
    titular = fields.Char(
        string=u'Nome de titular'
    )
    cpf_titular = fields.Char(
        string=u'CPF/CNPJ Titular'
    )
    valor = fields.Float(
        string=u'Valor',
        digits=(16, 2)
    )
    numero_cheque = fields.Char(
        string=u'Número do cheque'
    )
    pre_datado = fields.Date(
        string=u'Pré datado para'
    )
    data_recebimento = fields.Date(
        string=u'Data do recebimento'
    )
    state = fields.Selection(
        selection=[
            ('novo', u'Novo'),
            ('verificado', u'Verificado'),
            ('recebido', u'Recebido'),
            ('descontado', u'Descontado'),
            ('repassado', u'Repassado'),
            ('devolvido_b', u'Devolvido pelo banco'),
            ('devolvido_p', u'Devolvido ao parceiro'),
        ],
        string='Status',
        default='novo'
    )

    def verificar_cheque(self):
        self.mudar_estado('verificado')

    def cheque_recebido(self):
        self.mudar_estado('recebido')

    def cheque_descontado(self):
        self.mudar_estado('descontado')

    def cheque_repassado(self):
        self.mudar_estado('repassado')

    def cheque_devolvido_banco(self):
        self.mudar_estado('devolvido_b')

    def cheque_devolvido_parceiro(self):
        self.mudar_estado('devolvido_p')

    def mudar_estado(self, estado):
        permitido = [
            ('novo', 'verificado'),
            ('verificado', 'recebido'),
            ('recebido', 'descontado'),
            ('recebido', 'repassado'),
            ('recebido', 'devolvido_b'),
            ('devolvido_b', 'devolvido_p')
        ]
        if (self.state, estado) in permitido:
            self.state = estado

    @api.onchange('codigo')
    def onchange_codigo(self):
        if self.codigo and len(self.codigo) == 34:
            self.banco_id = self.env.get('res.bank').search([
                ('bic', '=', self.codigo[1:4])
            ])
            self.agencia = self.env.get('res.bank.agencia').search([
                ('name', '=', self.codigo[4:8])
            ])
            self.numero_cheque = self.codigo[13:19]
            self.conta = self.codigo[26:32]
