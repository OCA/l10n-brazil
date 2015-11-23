# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Payment Boleto module for Odoo
#    Copyright (C) 2012-2015 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Miléo <mileo@kmee.com.br>
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

from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    own_number_type = fields.Selection(
        [('0', u'Sequêncial único por empresa'),
         ('1', u'Numero sequêncial da Fatura'),
         ('2', u'Sequêncial único por modo de pagamento'), ],
        string=u'Tipo de nosso número', default='2')
    own_number_sequence = fields.Many2one('ir.sequence',
                                          string=u'Sequência do Nosso Número')
    transaction_id_sequence = fields.Many2one('ir.sequence',
                                              string=u'Sequência da fatura')
