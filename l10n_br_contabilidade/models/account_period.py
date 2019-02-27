# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import random
import string

from dateutil.relativedelta import relativedelta
from openerp import api, fields, models
from openerp.exceptions import Warning as UserError


class AccountPeriod(models.Model):
    _inherit = 'account.period'

    account_move_ids = fields.One2many(
        string=u'Lançamentos Contábeis',
        comodel_name='account.move',
        inverse_name='period_id',
        domain=[('lancamento_de_fechamento', '=', False)],
    )

    account_move_fechamento_ids = fields.One2many(
        string=u'Lançamentos Contábeis do Fechamento',
        comodel_name='account.move',
        inverse_name='period_id',
        domain=[('lancamento_de_fechamento', '=', True)],
    )

    account_fechamento_id = fields.Many2one(
        string=u'Fechamento',
        comodel_name='account.fechamento',
    )

    account_journal_id = fields.Many2one(
        string=u'Diário de fechamento',
        comodel_name='account.journal',
    )

    @api.multi
    def button_fechar_periodo(self):
        for record in self:
            record.fechar_periodo()

    @api.multi
    def fechar_periodo(self):
        """

        :return:
        """
        for record in self:
            # Altera estado
            record.state = 'done'

    @api.multi
    def reopen_period(self):
        """
        :return:
        """
        for record in self:
            for move in record.account_move_fechamento_ids:
                move.state = 'draft'

            record.account_move_fechamento_ids.unlink()

            for move in record.account_move_ids:
                move.lancamento_de_fechamento = False

            record.state = 'draft'
