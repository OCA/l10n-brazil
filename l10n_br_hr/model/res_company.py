# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Rafael da Silva Lima <rafael.lima@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.osv import orm, fields

class ResCompany(orm.Model):
    _inherit = 'res.company'
  
    _columns = {
        'check_benefits': fields.boolean('Valley Food and Meal Valley simultaneous', required=False),
       }