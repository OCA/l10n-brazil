# -*- encoding: utf-8 -*-
# #############################################################################
#
#    Account Payment Partner module for OpenERP
#    Copyright (C) 2012 KMEE (http://www.kmee.com.br)
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

from openerp import models, fields, api

class PaymentMode(models.Model):
    _inherit = 'payment.mode'

    type_payment = fields.Selection(
        [('00', 'Duplicata'),
         ('01', 'Cheque'),
         ('02', 'Promissória'),
         ('03', 'Recibo'),
         ('99', 'Outros')],
            string='Tipo SPED', required=True, default='99')