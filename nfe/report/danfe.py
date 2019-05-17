# -*- coding: utf-8 -*-
# Copyright (C) 2014 Rodolfo Leme Bertozo - KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from __future__ import with_statement
from odoo.report.render import render
from odoo.report.interface import report_int
from ..sped.nfe.processing.xml import print_danfe


class ExternalPdf(render):

    def __init__(self, pdf):
        render.__init__(self)
        self.pdf = pdf
        self.output_type = 'pdf'

    def _render(self):
        return self.pdf


class ReportCustom(report_int):
    '''
        Custom report for return danfe
    '''

    def create(self, cr, uid, ids, datas, context=None):
        context = context or {}
        active_ids = context.get('active_ids')
        # list_account_invoice = []

        ai_obj = self.env['account.invoice']
        account_invoice = ai_obj.browse(cr, uid, active_ids)
        # for account_invoice in ai_obj.browse(cr, uid, active_ids):
        #     list_account_invoice.append(account_invoice.id)

        pdf_string = print_danfe(account_invoice)

        self.obj = ExternalPdf(pdf_string)

        self.obj.render()
        return (self.obj.pdf, 'pdf')


ReportCustom('report.danfe_account_invoice')
