# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from ..constantes import *


class AccountAccount(models.Model):
    _inherit = 'account.account'
    _parent_name = 'parent_id'
    # _parent_store = True
    # _parent_order = 'code, name'
    # _order = 'parent_left, code'

    is_brazilian_account = fields.Boolean(
        string=u'Is a Brazilian Account?',
        compute='_compute_is_brazilian_account',
    )
    sped_empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
    )
    tipo = fields.Selection(
        selection=TIPO_CONTA_CONTABIL,
        string='Tipo',
        index=True,
    )
    parent_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta superior',
        ondelete='restrict',
        index=True,
    )
    parent_left = fields.Integer(
        string='Left Parent',
        index=True,
    )
    parent_right = fields.Integer(
        string='Right Parent',
        index=True,
    )
    child_ids = fields.One2many(
        comodel_name='account.account',
        inverse_name='parent_id',
        string='Contas inferiores',
    )
    data_inclusao = fields.Date(
        string='Data de inclusão',
        default=fields.Date.today,
        index=True,
    )
    data_alteracao = fields.Date(
        string='Data de alteração',
        index=True,
    )
    data_inativacao = fields.Date(
        string='Data de inativação',
        index=True,
    )
    nivel = fields.Integer(
        string='Nível',
        compute='_compute_conta_contabil',
        store=True,
        index=True,
    )
    natureza = fields.Selection(
        selection=NATUREZA_CONTA_CONTABIL,
        string='Natureza',
        compute='_compute_conta_contabil',
        store=True,
    )
    redutora = fields.Boolean(
        string='Redutora?',
        compute='_compute_conta_contabil',
        store=True,
    )
    tipo_sped = fields.Selection(
        selection=TIPO_SPED_CONTA_CONTABIL,
        string='Tipo no SPED Contábil',
        compute='_compute_conta_contabil',
        store=True,
    )
    nome_completo = fields.Char(
        string='Conta (completa)',
        size=500,
        compute='_compute_conta_contabil',
        store=True,
    )

    @api.depends('company_id', 'currency_id')
    def _compute_is_brazilian_account(self):
        for account in self:
            if account.company_id.country_id:
                if account.company_id.country_id.id == \
                        self.env.ref('base.br').id:
                    account.is_brazilian_account = True

                    #
                    # Brazilian accounts, by law, must always be in BRL
                    #
                    account.currency_id = self.env.ref('base.BRL').id

                    if account.company_id.sped_empresa_id:
                        account.sped_empresa_id = \
                            account.company_id.sped_empresa_id.id

                    continue

            account.is_brazilian_account = False

    @api.onchange('sped_empresa_id')
    def _onchange_sped_empresa_id(self):
        self.ensure_one()
        self.company_id = self.sped_empresa_id.company_id

    def _calcula_nivel(self):
        self.ensure_one()

        nivel = 1
        if self.parent_id:
            nivel += self.parent_id._calcula_nivel()

        return nivel

    def _calcula_nome(self):
        self.ensure_one()

        nome = self.name

        if self.parent_id:
            nome = self.parent_id._calcula_nome() + ' / ' + nome

        return nome

    @api.depends('parent_id', 'code', 'name', 'tipo', 'child_ids.parent_id')
    def _compute_conta_contabil(self):
        for conta in self:
            conta.nivel = conta._calcula_nivel()

            if conta.name and (conta.name.startswith('(-)')
                               or conta.name.startswith('( - )')):
                conta.redutora = True
            else:
                conta.redutora = False

            if len(conta.child_ids) > 0:
                conta.tipo_sped = 'S'
            else:
                conta.tipo_sped = 'A'

            if conta.code and conta.name:
                conta.nome_completo = conta.code + ' - ' + \
                                      conta._calcula_nome()

            if conta.tipo:
                conta.natureza = TIPO_CONTA_CONTABIL_NATUREZA[conta.tipo]

    @api.model
    def create(self, dados):
        if 'company_id' in dados:
            if 'sped_empresa_id' not in dados:
                company = self.env['res.company'].browse(dados['company_id'])

                if company.sped_empresa_id:
                    dados['sped_empresa_id'] = company.sped_empresa_id.id

        return super(AccountAccount, self).create(dados)