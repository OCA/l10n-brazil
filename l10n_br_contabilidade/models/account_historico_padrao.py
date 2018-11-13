# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from openerp import fields, models


class AccountHistoricoPadrao(models.Model):
    _name = 'account.historico.padrao'
    _description = 'Histórico padrão dos lançamentos contábeis'
    _order = 'name'

    name = fields.Char(
        string=u'Nome',
        required=True,
    )

    template_historico_padrao = fields.Char(
        string=u'Template para Histórico'
    )

    def get_historico_padrao(self, account_move_id=False, complemento=''):
        """
        :param account_move_id:
        :param complemento:
        :return:
        """
        if self.template_historico_padrao:
            hoje = datetime.today()
            historico_padrao = self.template_historico_padrao.replace(
                '%{AAAA}', str(hoje.year))
            historico_padrao = historico_padrao.replace(
                '%{AA}', str(hoje.year)[-2:])
            historico_padrao = historico_padrao.replace(
                '%{MM}', str(hoje.month))
            historico_padrao = historico_padrao.replace(
                '%{DD}', str(hoje.day))
            return historico_padrao
