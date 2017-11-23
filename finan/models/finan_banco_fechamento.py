from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from pybrasil.valor import formata_valor
from pybrasil.data import hoje


from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from ..constantes import *

class FinanBancoFechamento(models.Model):
    _name = b'finan.banco.fechamento'
    _description = 'Fechamento de Caixa'

#saldo inicial
    saldo_inicial = fields.Float(
        string='Saldo inicial',
    )
# saldo final
    saldo_final = fields.Float(
        string='Saldo final',

    
    )
#Movimentacoes
    extratos_ids = fields.One2many(
        comodel_name='finan.banco.extrato',
        inverse_name='banco_id',
        readonly=True,
    )
    # lancamento_id = fields.Many2one(
    #     comodel_name='finan.lancamento',
    #     string='Movimentos',
    #     index=True,
    # )
# banco
    banco_id = fields.Many2one(
        comodel_name='finan.banco',
        string='Banco/caixa',
        index=True,
        ondelete='restrict',
    )
# Quem fechou
    user_id = fields.Many2one(
        comodel_name='res.users',
        default=lambda self: self.env.user.id,
    )
# Quando fechou
    data_fechamento = fields.Date(
        string='Data do fechamento',
        default=fields.Date.context_today,
        index=True,
    )
#Inicio de periodo
    data_inicial = fields.Date(
        string='Data inicial',
        index=True,
    )
#Final de periodo
    data_final = fields.Date(
        string='Data final',
        index=True,
    )
# state
    state = fields.Selection(
        string='State',
        selection=[
        ('1', 'Aberto'),
        ('2', 'Fechado'),
        ],
    )


   