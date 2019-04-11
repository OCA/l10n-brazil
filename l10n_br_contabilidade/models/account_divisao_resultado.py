# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import Warning


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

    @api.model
    def create(self, vals):
        if vals.get('valor_fixo') and vals.get('porcentagem'):
            raise Warning(u'Só pode existir Valor Fixo ou Porcentagem. '
                          u'Necessário excluir e adicionar novamente a linha '
                          u'onde os dois valores estão preenchidos')

        return super(AccountDivisaoResultado, self).create(vals)

    @api.onchange('porcentagem')
    def onchange_porcentagem(self):
        self.ensure_one()
        self.porcentagem = 0 if self.valor_fixo != 0 else self.porcentagem

    @api.onchange('valor_fixo')
    def onchange_valor_fixo(self):
        self.ensure_one()
        self.valor_fixo = 0 if self.porcentagem != 0 else self.valor_fixo
