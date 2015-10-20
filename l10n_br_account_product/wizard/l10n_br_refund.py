# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Florian da Costa - Akretion                             #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp.osv import orm, fields
from lxml import etree

OPERATION_TYPE = {
    'out_invoice': 'output',
    'in_invoice': 'input',
    'out_refund': 'input',
    'in_refund': 'output'
}

JOURNAL_TYPE = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale_refund',
    'in_refund': 'purchase_refund'
}

class account_invoice_refund(orm.TransientModel):

    _inherit = "account.invoice.refund"
    _columns = {
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria Fiscal',
            domain="[('journal_type', '=', 'sale_refund'), ('fiscal_type', '=', 'product')]", required=True),
    }


    def compute_refund(self, cr, uid, ids, mode='refund', context=None):

        inv_obj = self.pool.get('account.invoice')
        line_obj = self.pool.get('account.invoice.line')
        if not context:
            context = {}

        for send_invoice in inv_obj.browse(cr, uid, context.get('active_ids'), context):

            fiscal_category_id = send_invoice.fiscal_category_id.refund_fiscal_category_id.id

            res = super(account_invoice_refund, self).compute_refund(cr, uid, ids, mode, context)
            domain = res['domain']

            ids_domain = [x for x in domain if x[0] == 'id'][0]
            invoice_ids = ids_domain[2]

            for invoice in inv_obj.browse(cr, uid, invoice_ids, context=context):
                
                line_ids = line_obj.search(cr, uid, [('invoice_id', '=', invoice.id)])

                if invoice.payment_term:
                    payment_term = invoice.payment_term.id
                else:
                    payment_term = False
                if invoice.partner_bank_id:
                    bank = invoice.partner_bank_id.id
                else:
                    bank = False
                onchange = inv_obj.onchange_partner_id(cr, uid, [invoice.id], 'out_refund', invoice.partner_id.id, invoice.date_invoice, payment_term, bank, invoice.company_id.id, fiscal_category_id)
                onchange['value']['fiscal_category_id'] = fiscal_category_id

                for idx, send_line in enumerate(send_invoice.invoice_line):

                    line_fiscal_category_id = send_line.fiscal_category_id.refund_fiscal_category_id.id
                    line_onchange = line_obj.onchange_fiscal_category_id(cr, uid, ids, invoice.partner_id.id,
                                     invoice.company_id.id, send_line.product_id.id, line_fiscal_category_id,
                                     send_line.account_id.id, context)
                    line_onchange['value']['fiscal_category_id'] = line_fiscal_category_id

                    line_obj.write(cr, uid, line_ids[idx],line_onchange['value'],context)
                inv_obj.write(cr, uid, [invoice.id], onchange['value'], context=context)
            return res



    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(account_invoice_refund, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        if not context:
            context = {}
        type = context.get('type', 'out_invoice')
        journal_type = JOURNAL_TYPE[type]
        type = OPERATION_TYPE[type]
        eview = etree.fromstring(res['arch'])
        fiscal_categ = eview.xpath("//field[@name='fiscal_category_id']")
        for field in fiscal_categ:
            field.set('domain', "[('journal_type', '=', '%s'),('fiscal_type', '=', 'product'), ('type', '=', '%s')]" % (journal_type, type,))
        res['arch'] = etree.tostring(eview)
        return res
