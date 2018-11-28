# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountSaldo(models.Model):
    _name = 'account.saldo'
    _order = 'account_account_id'
    _description = u'Modelo para guardar saldo das cotas no fechamento dos ' \
                   u'períodos.'

    name = fields.Char(
        string='Nome',
    )

    account_account_id = fields.Many2one(
        string=u'Conta',
        comodel_name='account.account',
    )

    saldo_inicial = fields.Float(
        string='Saldo Inicial',
        help=u'Saldo Inicial da conta no período',
    )

    debito_periodo = fields.Float(
        string=u'Débito',
        help=u'Total de débitos no período',
    )

    credito_periodo = fields.Float(
        string=u'Crédito',
        help=u'Total de créditos no período',
    )

    saldo_periodo = fields.Float(
        string='Total',
        help=u'Saldo de lançamentos no período',
    )

    saldo_final = fields.Float(
        string='Balanço',
        help=u'Saldo Final da conta no período.\n'
             u'Soma do saldo inicial e do saldo do período',
    )

    account_period_id = fields.Many2one(
        string=u'Período',
        comodel_name='account.period',
    )

    identificacao_saldo = fields.Selection(
        selection=[
            ('', ''),
            ('debito', 'D'),
            ('credito', 'C'),
        ],
        related='account_account_id.identificacao_saldo',
    )