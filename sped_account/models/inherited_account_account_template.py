# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from openerp.addons.l10n_br_base.models.sped_base import SpedBase
from ..constantes import *


class AccountAccountTemplate(SpedBase, models.Model):
    _inherit = 'account.account.template'

    is_brazilian = fields.Boolean(
        string=u'Is a Brazilian Account?',
    )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
    )
    tipo = fields.Selection(
        selection=TIPO_CONTA_CONTABIL,
        string='Tipo',
    )
    parent_id = fields.Many2one(
        comodel_name='account.account.template',
        string='Conta superior',
        ondelete='restrict',
        index=True,
    )

    @api.depends('company_id', 'currency_id', 'is_brazilian')
    def _compute_is_brazilian(self):
        for account in self:
            if account.company_id.country_id:
                if account.company_id.country_id.id == \
                        self.env.ref('base.br').id:
                    account.is_brazilian = True

                    #
                    # Brazilian accounts, by law, must always be in BRL
                    #
                    account.currency_id = self.env.ref('base.BRL').id

                    if account.company_id.empresa_id:
                        account.empresa_id = \
                            account.company_id.empresa_id.id

                    continue

            account.is_brazilian = False

    @api.onchange('empresa_id')
    def _onchange_empresa_id(self):
        self.ensure_one()
        self.company_id = self.empresa_id.company_id

    @api.model
    def create(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)
        return super(SaleOrder, self).create(dados)

    def write(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)
        return super(SaleOrder, self).write(dados)
