# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models

class AccountHistoricoPadrao(models.Model):
    _name = 'account.historico.padrao'
    _description = 'Histórico padrão dos lançamentos contábeis'
    _order = 'name'

    account_move_id = fields.One2many(
        string=u'Lançamento Contábil',
        comodel_name='account.move',
        inverse_name='historico_padrao_id',
    )

    name = fields.Char(
        string=u'Nome',
        required=True,
    )

    template_historico = fields.Char(
        string=u'Template para Histórico'
    )

    def get_historico_padrao(self, account_move_id, complemento=''):
        """

        :param account_move_id:
        :param complemento:
        :return:
        """
        return 'Historico Padrao'




