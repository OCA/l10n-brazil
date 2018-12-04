# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountDivisaoResultado(models.Model):
    _name = 'account.divisao.resultado'
    _description = 'Vincula Contas ao Fechamento para informar porcentagem'
    _order = 'account_id'
    _sql_constraints = [
        ('account_journal_ident_unique', 'unique(account_id, journal_id)',
         'Contas para Fechamento duplicadas.'),
    ]

    account_id = fields.Many2one(
        string=u'Conta',
        comodel_name='account.account',
    )

    journal_id = fields.Many2one(
        string=u'Diário',
        comodel_name='account.journal',
    )

    porcentagem = fields.Float(
        string=u'Porcentagem',
    )

    valor_fixo = fields.Float(
        string=u'Valor Fixo',
    )

    sequencia = fields.Integer(
        string=u'Sequência',
        default=1,
    )

