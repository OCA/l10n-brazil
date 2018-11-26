# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import random
import string

import pandas as pd
from openerp import api, fields, models
from openerp.exceptions import Warning as UserError


class AccountFechamento(models.Model):
    _name = 'account.fechamento'
    _description = 'Modelo para criar os lançamentos de fechamento de períodos'
    _order = 'name'

    name = fields.Char(
        string=u'Nome',
    )

    periodo_ini = fields.Many2one(
        comodel_name='account.period',
        string=u'Periodo - Início',
    )

    periodo_fim = fields.Many2one(
        comodel_name='account.period',
        string=u'Periodo - Fim',
    )

    account_period_ids = fields.One2many(
        string=u'Períodos',
        comodel_name='account.period',
        inverse_name='account_fechamento_id',
    )

    fiscalyear_id = fields.Many2one(
        comodel_name='account.fiscalyear',
        string='Ano base',
        default=lambda self: self._get_defaults(),
    )

    account_journal_id = fields.Many2one(
        string=u'Diário de fechamento',
        comodel_name='account.journal',
    )

    state = fields.Selection(
        selection=[
            ('open', 'Open'),
            ('close', 'Closed'),
        ],
        string='State',
        default='open',
    )

    def _get_defaults(self):
        fiscalyear_id = self.env['account.fiscalyear'].find()
        return fiscalyear_id

    @api.multi
    def button_buscar_periodos(self):
        """
        :return:
        """
        for record in self:

            # Buscar todos periodos no intervalo indicado
            period_ids = self.env['account.period'].search([
                ('date_start', '>=', record.periodo_ini.date_start),
                ('date_stop', '<=', record.periodo_fim.date_stop),
            ])

            # Validar para Não encontrar períodos fechados no intervalo
            peridos_fechados = period_ids.filtered(lambda x: x.state == 'done')
            if peridos_fechados:
                raise UserError(u'Períodos já encerrados no intervalo selecionado!')

            # Associa o periodo a este fechamento
            record.account_period_ids = period_ids


    @api.multi
    def button_fechar_periodos(self):
        for record in self:
            record.button_buscar_periodos()
            for period_id in record.mapped('account_period_ids'):
                period_id.fechar_periodo()

            record.state = 'close'


    @api.multi
    def button_reopen(self):
        for record in self:
            for period_id in record.mapped('account_period_ids'):
                period_id.reopen_period()

            record.account_period_ids = False
            record.state = 'open'
