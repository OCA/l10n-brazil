# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
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

from lxml import etree

from openerp.osv import orm
from openerp.addons.l10n_br_account.account_invoice import OPERATION_TYPE


class AccountInvoice(orm.Model):
    _inherit = 'account.invoice'

    def _default_fiscal_category(self, cr, uid, context=None):

        DEFAULT_FCATEGORY_SERVICE = {
            'in_invoice': 'in_invoice_service_fiscal_category_id',
            'out_invoice': 'out_invoice_service_fiscal_category_id'
        }

        default_fo_category = {
           'service': DEFAULT_FCATEGORY_SERVICE
        }

        invoice_type = context.get('type', 'out_invoice')
        invoice_fiscal_type = context.get('fiscal_type', 'product')

        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        fcategory = self.pool.get('res.company').read(
            cr, uid, user.company_id.id,
            [default_fo_category[invoice_fiscal_type][invoice_type]],
            context=context)[default_fo_category[invoice_fiscal_type][
                invoice_type]]

        return fcategory and fcategory[0] or False

    _defaults = {
        'fiscal_category_id': _default_fiscal_category,
    }


class AccountInvoiceLine(orm.Model):
    _inherit = 'account.invoice.line'

    def fields_view_get(self, cr, uid, view_id=None, view_type=False,
                        context=None, toolbar=False, submenu=False):

        result = super(AccountInvoiceLine, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu)

        if context is None:
            context = {}

        if view_type == 'form':
            eview = etree.fromstring(result['arch'])

            if 'type' in context.keys():
                cfops = eview.xpath("//field[@name='cfop_id']")
                for cfop_id in cfops:
                    cfop_id.set('domain', "[('type','=','%s')]" % (
                        OPERATION_TYPE[context['type']],))
                    cfop_id.set('required', '1')

            if context.get('fiscal_type', False) == 'service':

                cfops = eview.xpath("//field[@name='cfop_id']")
                for cfop_id in cfops:
                    cfop_id.set('invisible', '1')
                    cfop_id.set('required', '0')

            result['arch'] = etree.tostring(eview)

        return result
