# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_brazilian = fields.Boolean(
        string=u'Is a Brazilian Journal?',
        compute='_compute_is_brazilian',
        store=True,
    )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
    )

    @api.depends('company_id', 'currency_id')
    def _compute_is_brazilian(self):
        for journal in self:
            if journal.company_id.country_id:
                if journal.company_id.country_id.id == \
                        self.env.ref('base.br').id:
                    journal.is_brazilian = True

                    #
                    # Brazilian journals, by law, must always be in BRL
                    #
                    journal.currency_id = self.env.ref('base.BRL').id

                    if journal.company_id.empresa_id:
                        journal.empresa_id = journal.company_id.empresa_id

                    continue

            journal.is_brazilian = False

    @api.onchange('empresa_id')
    def _onchange_empresa_id(self):
        self.ensure_one()
        self.company_id = self.empresa_id.company_id

    @api.model
    def create(self, dados):
        if 'company_id' in dados and 'empresa_id' not in dados:
            company = self.env['res.company'].browse(dados['company_id'])

            if company.empresa_id:
                dados['empresa_id'] = company.empresa_id.id

        return super(AccountJournal, self).create(dados)

    def write(self, dados):
        if 'company_id' in dados and 'empresa_id' not in dados:
            company = self.env['res.company'].browse(dados['company_id'])

            if company.empresa_id:
                dados['empresa_id'] = company.empresa_id.id

        return super(AccountJournal, self).write(dados)
