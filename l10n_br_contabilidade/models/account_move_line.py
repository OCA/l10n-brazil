# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import Warning


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def create(self, vals):
        if not vals.get('debit') and not vals.get('credit'):
            raise Warning(
                'Não é possível criar lançamentos com debito/crédito zerado!'
            )

    @api.model
    def write(self, vals, check=False):
        for record in self:
            if vals.get('debit') == 0:
                if record.credit == 0:
                    raise Warning(
                        'Não é possível criar lançamentos com '
                        'debito/crédito zerado!'
                    )
            elif vals.get('credit') == 0:
                if record.debit == 0:
                    raise Warning(
                        'Não é possível criar lançamentos com '
                        'debito/crédito zerado!'
                    )

            return super(AccountMoveLine, record).write(vals)
