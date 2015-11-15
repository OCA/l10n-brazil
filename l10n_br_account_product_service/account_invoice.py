# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
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

from openerp.osv import orm, fields

from .l10n_br_account_product_service import PRODUCT_FISCAL_TYPE


class AccountInvoice(orm.Model):
    _inherit = 'account.invoice'

    def _get_fiscal_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('fiscal_type', 'product')

    _columns = {
        'fiscal_type': fields.selection(
            PRODUCT_FISCAL_TYPE, 'Tipo Fiscal', required=True),
    }

    def _default_fiscal_category(self, cr, uid, context=None):

        DEFAULT_FCATEGORY_PRODUCT = {
            'in_invoice': 'in_invoice_fiscal_category_id',
            'out_invoice': 'out_invoice_fiscal_category_id',
            'in_refund': 'in_refund_fiscal_category_id',
            'out_refund': 'out_refund_fiscal_category_id'
        }

        DEFAULT_FCATEGORY_SERVICE = {
            'in_invoice': 'in_invoice_service_fiscal_category_id',
            'out_invoice': 'out_invoice_service_fiscal_category_id'
        }

        default_fo_category = {
           'product': DEFAULT_FCATEGORY_PRODUCT,
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

    def _default_fiscal_document(self, cr, uid, context):
        invoice_fiscal_type = context.get('fiscal_type', 'product')
        fiscal_invoice_id = invoice_fiscal_type + '_invoice_id'

        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        fiscal_document = self.pool.get('res.company').read(
            cr, uid, user.company_id.id, [fiscal_invoice_id],
            context=context)[fiscal_invoice_id]

        return fiscal_document and fiscal_document[0] or False

    def _default_fiscal_document_serie(self, cr, uid, context):
        invoice_fiscal_type = context.get('fiscal_type', 'product')
        fiscal_document_serie = False
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company = self.pool.get('res.company').browse(
            cr, uid, user.company_id.id, context=context)

        if invoice_fiscal_type == 'product':
            fiscal_document_series = [doc_serie for doc_serie in
                                     company.document_serie_product_ids if
                                     doc_serie.fiscal_document_id.id ==
                                     company.product_invoice_id.id and
                                     doc_serie.active]
            if fiscal_document_series:
                fiscal_document_serie = fiscal_document_series[0].id
        else:
            fiscal_document_serie = company.document_serie_service_id and \
            company.document_serie_service_id.id or False

        return fiscal_document_serie

    _defaults = {
        'fiscal_type': _get_fiscal_type,
        'fiscal_category_id': _default_fiscal_category,
        'fiscal_document_id': _default_fiscal_document,
        'document_serie_id': _default_fiscal_document_serie
    }
