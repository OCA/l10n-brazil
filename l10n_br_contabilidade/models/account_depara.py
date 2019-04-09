# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountDePara(models.Model):
    _name = 'account.depara'
    _description = u'Mapeamento do plano de contas do sistemas para ' \
                   u'os "n" planos de contas necessários'
    _order = 'account_depara_plano_id, conta_sistema_id'

    name = fields.Char(
        string='Nome',
        compute='_get_display_name',
    )

    account_depara_plano_id = fields.Many2one(
        string='Plano de Contas',
        comodel_name='account.depara.plano',
    )

    conta_sistema_id = fields.Many2one(
        string='Conta Oficial',
        comodel_name='account.account',
        domain="[('account_depara_plano_id', '=', False)]",
    )

    conta_referencia_id = fields.Many2one(
        string='Conta Referência',
        comodel_name='account.account',
    )

    @api.multi
    def _get_display_name(self):
        for record in self:
            record.name = '{}: De: {} Para: {}'.format(
                record.account_depara_plano_id.name,
                record.conta_sistema_id.display_name,
                record.conta_referencia_id.display_name
            )
