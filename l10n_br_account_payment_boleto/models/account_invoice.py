# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Payment Boleto module for Odoo
#    Copyright (C) 2012-2015 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Miléo <mileo@kmee.com.br>
#    @author Danimar Ribeiro <danimaribeiro@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from openerp import models, fields, api

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_move_create(self):
        value = super(AccountInvoice, self).action_move_create()

        for invoice in self:
            sequence = self.env['ir.sequence'].next_by_id(
                self.company_id.own_number_sequence.id)
            invoice.transaction_id = sequence

        return value
