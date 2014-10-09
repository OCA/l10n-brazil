<<<<<<< HEAD
# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Rafael da Silva Lima <rafael.lima@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    check_benefits = fields.Boolean(u'Vale Refeição e Vale Alimentação',
                                    required=False)
=======
# -*- encoding: utf-8 -*-
##############################################################################
#
#    Brazillian Human Resources Payroll module for OpenERP
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Rafael da Silva Lima <rafael.lima@kmee.com.br>
#            
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
from osv import fields,osv

class ResCompany(osv.osv):
    _inherit = 'res.company'
  
    _columns = {
        'check_benefits': fields.boolean('Valley Food and Meal Valley simultaneous', required=False),
       }
>>>>>>> [NEW] Modulo de localicazão dos recursos humanos
