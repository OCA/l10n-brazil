from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from pybrasil.valor import formata_valor
from pybrasil.data import hoje
from odoo.exceptions import ValidationError


from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from ..constantes import *

class FinanBancoFechamento(models.Model):
    _name = b'finan.banco.fechamento'
    _description = 'Fechamento de Caixa'

    saldo_inicial = fields.Float(
        string='Saldo inicial',
    )

    saldo_final = fields.Float(
        string='Saldo final',
        # compute = '_compute_saldo_final'
    )

    lancamento_ids = fields.Many2many(
        string='Pagamentos',
        comodel_name='finan.lancamento',
        readonly=True,
        states={'aberto': [('readonly', False)]},
    )

    saldo = fields.Float(
        string="Saldo dos lancamentos"
    )

    banco_id = fields.Many2one(
        comodel_name='finan.banco',
        string='Banco/caixa',
        index=True,
        ondelete='restrict',
        required=True,
    )

    user_id = fields.Many2one(
        string='Quem fechou?',
        comodel_name='res.users',
        default=lambda self: self.env.user.id,
        required=True,
    )

    data_fechamento = fields.Date(
        string='Data do fechamento',
        index=True,
        readonly=True,
    )

    data_inicial = fields.Date(
        string='Data inicial',
        index=True,
        required=True,
    )

    data_final = fields.Date(
        string='Data final',
        index=True,
        required=True,
    )

    state = fields.Selection(
        string='State',
        selection=[
            ('aberto', 'Aberto'),
            ('fechado', 'Fechado'),
        ],
        default='aberto',
    )


    @api.constrains('data_final', 'data_inicial')
    def _constrains_verifica_data(self):
        """
        Validacao para a data final ser maior que a data inicial
        """
        for record in self:
            if record.data_inicial > record.data_final:
                raise ValidationError(
                    'A data final deve ser maior que a data inicial')


    def button_processar(self):
        for fechamento in self:
            lancamento_ids = self.env.get('finan.lancamento').search([
                ('banco_id', '=', fechamento.banco_id.id),
                ('data_pagamento', '>=', fechamento.data_inicial),
                ('data_pagamento', '<=', fechamento.data_final),
                ('tipo', 'in', ['recebimento','pagamento']),
            ])
            fechamento.lancamento_ids = lancamento_ids

            for record in lancamento_ids:
                self.saldo_final = self.saldo_final + record.vr_documento


    def button_fechar_caixa(self):
        """
        Rotina para fechamento de caixa onde altera o state do fechamento
        """
        for banco in self:
            banco.state = 'fechado'
            banco.data_fechamento = fields.Date.today()

    # def _compute_saldo_final(self):
    #     """
    #             Calculo do saldo final: movimentos + inicial
    #     """
    #     for banco in self:
    #         saldo = self.env['finan.banco.saldo'].search([
    #             ('banco_id', '=', banco.id),
    #             ('data', '<=', str(hoje())),
    #         ], limit=1, order='data desc')
    #         if saldo:
    #             self.saldo_final = saldo.saldo + self.saldo_inicial
    #         else:
    #             self.saldo_final = self.saldo_inicial

