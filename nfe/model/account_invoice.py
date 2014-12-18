# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2014  KMEE - www.kmee.com.br - Rodolfo Leme Bertozo           #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU General Public License for more details.                                 #
#                                                                             #
#You should have received a copy of the GNU General Public License            #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

import pysped
import os
from StringIO import StringIO
from openerp.osv import orm
from report.pyPdf import PdfFileReader, PdfFileWriter
from openerp.addons.nfe.sped.nfe.processing.xml import monta_caminho_nfe


class account_invoice(orm.Model):
    _inherit = "account.invoice"

    def str_pdf_Danfes(self, cr, uid, ids, context=None):

        str_pdf = ""
        paths = []

        for inv in self.browse(cr, uid, ids):

            company = self.pool.get('res.company').browse(
                cr, uid, inv.company_id.id)
            nfe_key = inv.nfe_access_key
            procnfe = pysped.nfe.manual_401.ProcNFe_200()

            try:
                if inv.state in ['open', 'paid', 'sefaz_cancelled']:
                    file_xml = os.path.join(monta_caminho_nfe(
                        company, chave_nfe=nfe_key))

                else:
                    file_xml = os.path.join(os.path.join(
                        monta_caminho_nfe(company, chave_nfe=nfe_key), 'tmp/'))

                procnfe.xml = os.path.join(file_xml, nfe_key + '-nfe.xml')
            except:
                raise orm.except_orm(('Error !'),
                                     ('Não é possível gerar a Danfe '
                                      '- Confirme o Documento'))

            # try:
            #     for inv_doc_event in inv.account_document_event_ids:
            #         if inv_doc_event.file_sent:
            #             file_xml = inv_doc_event.file_sent
            #             break
            #     procnfe.xml = file_xml
            # except:
            #     raise orm.except_orm(('Error !'),
            #                          ('Não é possível gerar a Danfe '
            #                           '- Confirme o Documento'))

            danfe = pysped.nfe.processador_nfe.DANFE()
            danfe.NFe = procnfe.NFe
            danfe.protNFe = procnfe.protNFe
            danfe.caminho = "/tmp/"
            danfe.gerar_danfe()
            paths.append(danfe.caminho + danfe.NFe.chave + '.pdf')

        output = PdfFileWriter()
        s = StringIO()

        # merge dos pdf criados
        for path in paths:
            pdf = PdfFileReader(file(path, "rb"))

            for i in range(pdf.getNumPages()):
                output.addPage(pdf.getPage(i))

            output.write(s)

        str_pdf = s.getvalue()
        s.close()

        return str_pdf

    def invoice_print(self, cr, uid, ids, context=None):

        for inv in self.browse(cr, uid, ids, context):

            document_serie_id = inv.document_serie_id
            fiscal_document_id = inv.document_serie_id.fiscal_document_id
            electronic = inv.document_serie_id.fiscal_document_id.electronic

            if (document_serie_id and fiscal_document_id and not electronic):
                return super(account_invoice, self).invoice_print(
                    cr, uid, ids, context=context)

            assert len(ids) == 1, 'This option should only be ' \
                                  'used for a single id at a time.'
            self.write(cr, uid, ids, {'sent': True}, context=context)
            datas = {
                'ids': ids,
                'model': 'account.invoice',
                'form': self.read(cr, uid, ids[0], context=context)
            }

            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'danfe_account_invoice',
                'datas': datas,
                'nodestroy': True
            }
