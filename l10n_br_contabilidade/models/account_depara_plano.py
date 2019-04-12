# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountDeParaPlano(models.Model):
    _name = 'account.depara.plano'
    _description = u'Referência dos Planos de Contas Externos'

    name = fields.Char(
        string='Plano de Contas',
    )

    account_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta Principal',
    )

    @api.model
    def create(self, vals):
        """
        :param vals:
        :return:
        """

        account_account_id = self.env['account.account'].create({
            'code': '0',
            'name': vals.get('name'),
            'type': 'view',
            'user_type': self.env.ref('account.data_account_type_view').id,
        })

        vals.update(account_account_id=account_account_id.id)

        account_depara_plano_id = super(AccountDeParaPlano, self).create(vals)

        account_account_id.account_depara_plano_id = account_depara_plano_id

        return account_depara_plano_id
