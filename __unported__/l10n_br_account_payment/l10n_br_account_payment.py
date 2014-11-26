# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2011  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

from openerp.osv import fields, orm


class payment_line(orm.Model):
    _inherit = 'payment.line'
    _columns = {
        'related_mode_id': fields.related(
            'order_id', 'mode', type='many2one', relation='payment.mode',
            string='Payment Mode', store=True, readonly=True),
    }


class account_move_line(orm.Model):
    _inherit = 'account.move.line'

    def _payment_mode_search(self, cr, uid, obj, name, args, context):
        if not len(args):
            return []
        operator = args[0][1]
        value = args[0][2]
        if not value:
            return []
        if isinstance(value, int) or isinstance(value, long):
            ids = [value]
        elif isinstance(value, list):
            ids = value
        else:
            ids = self.pool.get('payment.mode').search(cr,uid,[('id','=',value)], context=context)
        if ids:
            cr.execute('SELECT l.move_line_id ' \
                'FROM payment_line l ' \
                'WHERE l.related_mode_id in (%s)' % (','.join(map(str, ids))))
            res = cr.fetchall()
            if len(res):
                return [('id', 'in', [x[0] for x in res])]
        return [('id','=','0')]

    def _payment_mode_get(self, cr, uid, ids, field_name, arg, context={}):
        result = {}
        line_obj = self.pool.get('payment.line')
        for rec in self.browse(cr, uid, ids, context):
            result[rec.id] = (0,0)
            payment_line_id = line_obj.search(cr, uid, [('move_line_id', '=', rec.id)], context=context)
            if payment_line_id:
                line = line_obj.browse(cr, uid, payment_line_id[0], context)
                if line.related_mode_id:
                    result[rec.id] = (line.related_mode_id.id, self.pool.get('payment.mode').browse(cr, uid, line.related_mode_id.id, context).name)
            else:
                result[rec.id] = (0, 0)
        return result

    _columns = {
        'related_mode_id': fields.function(_payment_mode_get, method=True,
            fnct_search=_payment_mode_search, type="many2one",
            relation="payment.mode", string="Payment Mode", readonly=True),
    }
