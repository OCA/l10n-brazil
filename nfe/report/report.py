# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2014 Rodolfo Leme Bertozo - KMEE - www.kmee.com.br            #
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

from __future__ import with_statement
from openerp.report.render import render
from openerp.report.interface import report_int
from openerp import pooler
from openerp.addons.nfe.sped.nfe.processing.xml import print_danfe


class external_pdf(render):

    def __init__(self, pdf):
        render.__init__(self)
        self.pdf = pdf
        self.output_type = 'pdf'

    def _render(self):
        return self.pdf


class report_custom(report_int):
    '''
        Custom report for return danfe
    '''

    def create(self, cr, uid, ids, datas, context={}):
        active_ids = context.get('active_ids')
        pool = pooler.get_pool(cr.dbname)
        # list_account_invoice = []

        ai_obj = pool.get('account.invoice')
        account_invoice = ai_obj.browse(cr, uid, active_ids)
        # for account_invoice in ai_obj.browse(cr, uid, active_ids):
        #     list_account_invoice.append(account_invoice.id)

        pdf_string = print_danfe(account_invoice)

        self.obj = external_pdf(pdf_string)

        self.obj.render()
        return (self.obj.pdf, 'pdf')

report_custom('report.danfe_account_invoice')
