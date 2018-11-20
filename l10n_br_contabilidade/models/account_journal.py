# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    template_historico_padrao_id = fields.Many2one(
        string=u'Template Padrão do Lançamento',
        comodel_name='account.historico.padrao',
    )

    fechamento_debit_account_id = fields.Many2one(
        string=u'Conta de Débito para fechamento',
        comodel_name='account.account',
    )

    fechamento_credit_account_id = fields.Many2one(
        string=u'Conta de Crédito para fechamento',
        comodel_name='account.account',
    )
