# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import with_statement, unicode_literals

from openerp import pooler
from openerp.osv import osv
from openerp.report.interface import report_int
from openerp.report.render import render

from ..febraban.boleto.document import Boleto

class ExternalPdf(render):

    def __init__(self, pdf):
        render.__init__(self)
        self.pdf = pdf
        self.output_type = 'pdf'

    def _render(self):
        return self.pdf


class ReportCustom(report_int):
    """
        Custom report for return boletos
    """

    def create(self, cr, uid, ids, datas, context=False):
        if not context:
            context = {}
        active_ids = context.get('active_ids')
        active_model = context.get('active_model')
        pool = pooler.get_pool(cr.dbname)
        ids_financial_lines = []

        financial_obj = pool.get('financial.move')

        if active_model == 'account.invoice':
            ai_obj = pool.get('account.invoice')
            for account_invoice in ai_obj.browse(cr, uid, active_ids):
                for move_line in account_invoice.financial_ids:
                    ids_financial_lines.append(move_line.id)
        elif active_model == 'financial.move':
            ids_financial_lines = active_ids
        else:
            return False

        boleto_list = financial_obj.gera_boleto(cr, uid, ids_financial_lines)
        if not boleto_list:
            raise osv.except_osv(
                'Error !', ('Não é possível gerar os boletos\n'
                            'Certifique-se que a fatura esteja confirmada e o '
                            'forma de pagamento seja duplicatas'))
        pdf_string = Boleto.get_pdfs(boleto_list)
        self.obj = ExternalPdf(pdf_string)
        self.obj.render()
        return self.obj.pdf, 'pdf'


ReportCustom('report.l10n_br_financial_payment_order.report')
