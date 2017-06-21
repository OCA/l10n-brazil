# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from ..constantes import *


class AccountAccountType(models.Model):
    _inherit = 'account.account.type'

    is_brazilian_account_type = fields.Boolean(
        string=u'Is a Brazilian Account?',
    )
    redutor = fields.Boolean(
        string='Redutor?',
        compute='_compute_redutor',
        store=True,
    )

    @api.depends('name')
    def _compute_redutor(self):
        for account_type in self:
            if account_type.name and (account_type.name.startswith('(-)')
                                      or account_type.name.startswith('( - )')):
                account_type.redutor = True
            else:
                account_type.redutor = False

    @api.multi
    def name_get(self):
        res = []

        for account_type in self:
            nome = account_type.name

            if account_type.is_brazilian_account_type:
                nome += ' - ' + account_type.note

            res.append((account_type.id, nome))

        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name and operator in ('=', 'ilike', '=ilike', 'like'):
            if operator != '=':
                name = name.strip().replace(' ', '%')

            args += [
                '|',
                ('name', 'ilike', name),
                ('note', 'ilike', name),
            ]
            account_types = self.search(args, limit=limit)
            return account_types.name_get()

        return super(AccountAccountType, self).name_search(name=name,
                                                           args=args,
                                                           operator=operator,
                                                           limit=limit)
