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

#saldo inicial
    saldo_inicial = fields.Float(
        string='Saldo inicial',
        required=True,
    )
# saldo final
    saldo_final = fields.Float(
        string='Saldo final',
        compute='_compute_saldo_atual',

    
    )
#Movimentacoes
    extratos_ids = fields.One2many(
        comodel_name='finan.banco.extrato',
        inverse_name='banco_id',
        readonly=True,
        # compute='_compute_movimento_periodo',
    )

# banco
    banco_id = fields.Many2one(
        comodel_name='finan.banco',
        string='Banco/caixa',
        index=True,
        ondelete='restrict',
        required=True,
    )
# Quem fechou
    user_id = fields.Many2one(
        comodel_name='res.users',
        default=lambda self: self.env.user.id,
        required=True,
    )
# Quando fechou
    data_fechamento = fields.Date(
        string='Data do fechamento',
        default=fields.Date.context_today,
        index=True,
        required=True,
    )
#Inicio de periodo
    data_inicial = fields.Date(
        string='Data inicial',
        index=True,
        required = True,
    )
#Final de periodo
    data_final = fields.Date(
        string='Data final',
        index=True,
        required=True,
    )
# state
    state = fields.Selection(
        string='State',
        selection=[
        ('1', 'Aberto'),
        ('2', 'Fechado'),
        ],
        required=True,
    )

    @api.depends('banco', 'agencia', 'conta', 'conta_digito', 'tipo',
                 'titular_id')
    def _compute_banco(self):
        for banco in self:
            banco.nome = banco.name_get()[0][1]

    def _compute_saldo_atual(self):
        for banco in self:
            saldo = self.env['finan.banco.saldo'].search([
                ('banco_id', '=', banco.id),
                ('data', '<=', str(hoje())),
                ], limit=1, order='data desc')
            if saldo:
                self.saldo_final = saldo.saldo + self.saldo_inicial
            else:
                self.saldo_final = self.saldo_inicial

    @api.constrains('data_final', 'data_inicial')
    def _compute_verifica_data(self):
        for record in self:
            if record.data_inicial > record.data_final:
                raise ValidationError('A data final deve ser maior que a '
                                  'data inicial')

    # def _compute_movimento_periodo(self):
    #     for record in self:
    #         if record.data_inicial < 'finan.banco.extrato'.data and record.data_final > 'finan.banco.extrato'.data:
    #