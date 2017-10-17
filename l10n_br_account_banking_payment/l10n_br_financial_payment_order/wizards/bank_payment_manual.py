# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2009 EduSense BV (<http://www.edusense.nl>).
#              (C) 2011 - 2013 Therp BV (<http://therp.nl>).
#
#    All other contributions are (C) by their respective contributors
#
#    All Rights Reserved
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

"""This module contains a single "wizard" for confirming manual
bank transfers.
"""

from openerp import models, api, workflow


class PaymentManual(models.TransientModel):
    _inherit = 'payment.manual'
    _description = 'Send payment order(s) manually'

    @api.multi
    def button_ok(self):
        for order_id in self.env.context.get('active_ids', []):
            workflow.trg_validate(self.env.uid, 'payment.order', order_id,
                                  'generated', self.env.cr)
        return {'type': 'ir.actions.act_window_close'}
