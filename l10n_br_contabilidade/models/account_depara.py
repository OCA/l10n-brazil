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

    conta_referencia_id = fields.Many2one(
        string='Conta Referência',
        comodel_name='account.account',
    )

    conta_sistema_id = fields.Many2many(
        comodel_name='account.account',
        relation='account_depara_conta_sistema_rel',
        column1='account_depara_id',
        column2='conta_sistema_id',
        string='Conta Oficial',
        domain="[('account_depara_plano_id', '=', False)]",
    )

    @api.multi
    def _get_display_name(self):
        for record in self:
            record.name = 'DePara: {} - {}'.format(
                record.account_depara_plano_id.name,
                record.conta_referencia_id.display_name,
            )
