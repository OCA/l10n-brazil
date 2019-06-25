# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)

from openerp import api, fields, models


class WizardVerificationAccountDepara(models.TransientModel):
    _name = 'wizard.verification.account.depara'

    account_root_id = fields.Many2one(
        comodel_name='account.account',
        string='Plano de Contas Oficial',
        domain=[('parent_id', '=', False)],
        required=True,
        default=lambda self: self.default_get_root_account(),
    )

    chart_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Referência',
        domain=[('parent_id', '=', False)],
        required=True,
    )

    erro_relatorio = fields.Html(
        string='Realatório',
        readonly=True
    )

    def default_get_root_account(self):
        root_account_id =  self.env['account.account'].search([
            ('parent_id', '=', False),
        ], order='id ASC', limit=1)
        return root_account_id

    def _get_all_account_ids(self, parent_id):
        if parent_id.mapped('child_parent_ids'):
            return \
                parent_id + \
                self._get_all_account_ids(parent_id.mapped('child_parent_ids'))
        else:
            return parent_id

    @api.multi
    def analisar_plano_oficial(self):
        """
        Verificar se todas as contas do plano de contas OFICIAL estão
        vinculadas a pelo menos uma conta referencia
        """
        erro_depara = ''
        contas = self._get_all_account_ids(self.account_root_id)
        contas = contas.filtered(lambda x: x.type=='other')

        for conta in contas:
            depara_id = self.env['account.depara'].search([
                ('conta_sistema_id','in', conta.id),
            ])
            if not depara_id:
                erro_depara += \
                    '<p> {} - {} </p>'.format(conta.code, conta.name)

        if not erro_depara:
            erro_depara += 'OK! Tudo parece válido'

        self.erro_relatorio = '<h1>Plano de Contas: {}</h1> <br/> {}'.format(
            self.account_root_id.name, erro_depara)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Contas Oficiais sem mapeamento com '
                    'plano de contas externo',
            'res_model': 'wizard.verification.account.depara',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    @api.multi
    def analisar_plano_externo(self):
        """
        Verificar se todas as ontas do plano de contas externo estão
        vinculadas a pelo menos uma conta oficial
        """
        erro_depara = ''
        contas = self._get_all_account_ids(self.chart_account_id)
        contas = contas.filtered(lambda x: x.type=='other')

        for conta in contas:
            depara_id = self.env['account.depara'].search([
                ('conta_referencia_id','=',conta.id),
            ])
            if not depara_id:
                erro_depara += \
                    '<p> {} - {} </p>'.format(conta.code, conta.name)

        if not erro_depara:
            erro_depara += 'OK! Tudo parece válido'

        self.erro_relatorio = '<h1>Plano de Contas: {}</h1> <br/> {}'.format(
            self.chart_account_id.name, erro_depara)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Contas externas sem mapeamento'
                    ' para Plano de contas oficial',
            'res_model': 'wizard.verification.account.depara',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    @api.multi
    def analisar_duplicidade(self):
        """
        """
        erro_depara = ''
        contas = self._get_all_account_ids(self.chart_account_id)
        contas = contas.filtered(lambda x: x.type == 'other')

        for conta in contas:
            depara_id = self.env['account.depara'].search([
                ('conta_referencia_id','=',conta.id),
            ])
            if len(depara_id) > 1:
                erro_depara += \
                    '<p> {} - {} </p>'.format(conta.code, conta.name)


        contas = self._get_all_account_ids(self.account_root_id)
        contas = contas.filtered(lambda x: x.type == 'other')

        for conta in contas:
            depara_id = self.env['account.depara'].search([
                ('conta_sistema_id','in',conta.id),
            ])
            if len(depara_id) > 1:
                erro_depara += \
                    '<p> {} - {} </p>'.format(conta.code, conta.name)

        self.erro_relatorio = '<h1>Contas Duplicadas:</h1> <br/> {}'.\
            format(erro_depara)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Contas em Duplicidade no DePara',
            'res_model': 'wizard.verification.account.depara',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
