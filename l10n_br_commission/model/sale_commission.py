# -*- coding: utf-8 -*-
###############################################################################
# Copyright (C) 2015  KMEE  - www.kmee.com.br - Bertozo                       #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp.osv import orm


class SettlementAgent(orm.Model):

    _inherit = 'settlement.agent'

    def condition_state_invoice(self, cr, uid, ids, state, condition,
                                context=None):

        #state of invoice to pay commissions (one or more states)
        state = ['paid']
        #conditions of states (=, <>, in)
        condition = '='

        return super(SettlementAgent,
                     self).condition_state_invoice(cr, uid, ids, state,
                                                   condition, context=None)
