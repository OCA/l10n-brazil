# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountFechamento(models.Model):
    _name = 'account.fechamento'
    _description = 'Modelo para criar os lançamentos de fechamento de períodos'
    _order = 'name'

    name = fields.Char(
        string=u'Nome',
    )

    account_period_ids = fields.Many2many(
        string=u'Períodos',
        comodel_name='account.period',
    )

    fiscalyear_id = fields.Many2one(
        comodel_name='account.fiscalyear',
        string='Ano base',
    )

    account_move_ids = fields.One2many(
        string=u'Lançamentos Contábeis',
        comodel_name='account.move',
        inverse_name='account_fechamento_id',
        domain=[('lancamento_de_fechamento', '=', False)],
    )

    account_move_fechamento_ids = fields.One2many(
        string=u'Lançamentos Contábeis de Fechamento',
        comodel_name='account.move',
        inverse_name='account_fechamento_id',
        domain=[('lancamento_de_fechamento', '=', True)],
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

    @api.multi
    def button_fechar_periodos(self):
        """

        :return:
        """
        for record in self:
            record.state = 'close'

    @api.multi
    def button_buscar_lancamentos_do_periodo(self):
        """

        :return:
        """
        for record in self:

            # Desfazer relacionamento
            record.account_move_ids = False

            # Lançamentos que não estao em nenhum fechamento
            account_move_ids = self.env['account.move'].search([
                ('period_id','in', record.account_period_ids.ids),
                ('state','=','posted'),
                ('account_fechamento_id', '=', False),
            ])

            # Relacionar os lancamentos ao fechamento atual
            for account_move_id in account_move_ids:
                account_move_id.account_fechamento_id = record.id
