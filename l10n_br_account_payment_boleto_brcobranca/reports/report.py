# -*- coding: utf-8 -*-
# Copyright 2017 Akretion
# @author Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import with_statement

from openerp import pooler
from openerp.osv import osv
from openerp.report.interface import report_int
from openerp.report.render import render

#from ..boleto.document import Boleto

from openerp.exceptions import Warning as UserError
import requests
import json
import tempfile


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
        ids_move_lines = []

        aml_obj = pool.get('account.move.line')

        if active_model == 'account.invoice':
            ai_obj = pool.get('account.invoice')
            for account_invoice in ai_obj.browse(cr, uid, active_ids):
                for move_line in account_invoice.move_line_receivable_id:
                    ids_move_lines.append(move_line.id)
        elif active_model == 'account.move.line':
            ids_move_lines = active_ids
        else:
            return False

        boleto_list = aml_obj.send_payment(cr, uid, ids_move_lines)
        if not boleto_list:
            raise osv.except_osv(
                'Error !', ('Não é possível gerar os boletos\n'
                            'Certifique-se que a fatura esteja confirmada e o '
                            'forma de pagamento seja duplicatas'))

        boletos = [b.boleto_cnab_api_data for b in boleto_list]
        content = json.dumps(boletos)
        print content
        f = open(tempfile.mktemp(), 'w')
        f.write(content)
        f.close()
        files = {'data': open(f.name, 'rb')}
        res = requests.post("http://boleto_cnab_api:9292/api/boleto/multi",
                            data={'type': 'pdf'}, files=files)
        print "AAAAAAAA", res.status_code
        if str(res.status_code)[0] == '2':
            pdf_string = res.content
#           return res.content
        else:
           raise UserError(res.text.encode('utf-8'))

#           pdf_string = Boleto.get_pdfs(boleto_list)
        self.obj = ExternalPdf(pdf_string)
        self.obj.render()
        return self.obj.pdf, 'pdf'


ReportCustom('report.l10n_br_account_payment_boleto_brcobranca.report')
