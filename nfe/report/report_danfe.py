# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2016 Trustcode - www.trustcode.com.br                         #
#              Danimar Ribeiro <danimaribeiro@gmail.com>                      #
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
#                                                                             #
###############################################################################

from __future__ import with_statement

import base64
from StringIO import StringIO

from odoo.exceptions import Warning as UserError
from odoo.report.interface import report_int
from odoo.report.render import render
from pyPdf import PdfFileReader, PdfFileWriter


def print_danfe(xml_nfe):
    from pysped.nfe.leiaute import ProcNFe_310
    from pysped.nfe.danfe import DANFE
    procnfe = ProcNFe_310()

    paths = []
    procnfe.xml = xml_nfe
    danfe = DANFE()
    danfe.NFe = procnfe.NFe
    danfe.protNFe = procnfe.protNFe
    danfe.caminho = "/tmp/"
    danfe.gerar_danfe()
    paths.append(danfe.caminho + danfe.NFe.chave + '.pdf')

    output = PdfFileWriter()
    s = StringIO()

    for path in paths:
        pdf = PdfFileReader(file(path, "rb"))
        for i in range(pdf.getNumPages()):
            output.addPage(pdf.getPage(i))
        output.write(s)

    str_pdf = s.getvalue()
    s.close()
    return str_pdf


class ExternalPdf(render):
    def __init__(self, pdf):
        render.__init__(self)
        self.pdf = pdf
        self.output_type = 'pdf'

    def _render(self):
        return self.pdf


class CustomReportDanfe(report_int):
    def create(self, cr, uid, ids, datas, context=None):

        nfe_obj = self.env['nfe.mde']
        attach_obj = self.env['ir.attachment']
        nfe_mde = nfe_obj.browse(cr, uid, ids, context=context)
        attach_ids = attach_obj.search(cr, uid, [
            ('res_id', '=', nfe_mde.id),
            ('res_model', '=', 'nfe.mde'),
            ('name', '=like', 'NFe%')], context=context)

        if len(attach_ids) == 0:
            raise UserError(
                u'Atenção!',
                u'Nenhum xml de NFe anexado a este manifesto')
        attach = attach_obj.browse(cr, uid, attach_ids[0], context=context)
        pdf_string = print_danfe(
            base64.b64decode(
                attach.datas).decode("utf-8"))

        self.obj = ExternalPdf(pdf_string)
        self.obj.render()
        return (self.obj.pdf, 'pdf')


CustomReportDanfe('report.danfe_nfe_mde')
