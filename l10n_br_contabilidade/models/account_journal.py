# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    name = fields.Char(
        string=u'Nome do Lote',
    )

    template_historico_padrao_id = fields.Many2one(
        string=u'Template Padrão do Lançamento',
        comodel_name='account.historico.padrao',
    )

    journal_account_ids = fields.One2many(
        string=u'Contas para fechamento',
        comodel_name='account.journal.account',
        inverse_name='journal_id',
    )


class AccountJournalAccount(models.Model):
    _name = 'account.journal.account'
    _description = 'Vincula Contas ao Fechamento para informar porcentagem'
    _order = 'account_id'

    account_id = fields.Many2one(
        string=u'Conta',
        comodel_name='account.account',
    )

    journal_id = fields.Many2one(
        string=u'Diário',
        comodel_name='account.journal',
    )

    identificacao = fields.Selection(
        string='Identificação de Fechamanto',
        selection=[
            ('', ''),
            ('debito', 'Débito'),
            ('credito', 'Crédito'),
        ],
    )

    porcentagem = fields.Float(
        string=u'Porcentagem'
    )
