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


    def tratar_dicionario(self,complemento):
        """

        :param complemento:
        :return:
        """
        complement = {}
        for key in complemento:
            if isinstance(complemento.get(key), tuple):
                complement.update({key: complemento.get(key)[1]})
            else:
                complement.update({key:complemento.get(key)})

        return complement

    def get_historico_padrao(
            self, account_move_id=False,
            account_move_line_id=False, complemento={}):
        """
        :param account_move_id:
        :param complemento:
        :return:
        """
        historico_padrao = ''
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

            historico_padrao = historico_padrao.replace(
                '%{DD}', str(hoje.day))

            complemento = self.tratar_dicionario(complemento)

            if complemento:
                try:
                    historico_padrao = historico_padrao.format(
                        **complemento)
                except:
                    pass

            if account_move_id:
                try:
                    historico_padrao = historico_padrao.format(
                        **account_move_id.read()[0])
                except:
                    pass

            if account_move_line_id:
                try:
                    historico_padrao = historico_padrao.format(
                        **account_move_line_id.read()[0])
                except:
                    pass

        return historico_padrao
