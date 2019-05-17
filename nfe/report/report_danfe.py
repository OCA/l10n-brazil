# -*- coding: utf-8 -*-
# Copyright (C) 2016 Trustcode - www.trustcode.com.br
#       Danimar Ribeiro <danimaribeiro@gmail.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

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
