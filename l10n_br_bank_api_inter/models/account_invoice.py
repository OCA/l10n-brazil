# Copyright 2021 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import tempfile
from base64 import b64decode, b64encode
from PyPDF2 import PdfFileMerger

from odoo import api, fields, models, _


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    pdf_boletos_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='PDF Boletos',
        ondelete='cascade'
    )

    def _merge_pdf_boletos(self):
        pdf_merger = PdfFileMerger()

        temp_files = []
        for move_line in self.move_line_receivable_ids:
            move_line.generate_pdf_boleto()

            if move_line.pdf_boleto_id:
                temp_pdf = tempfile.TemporaryFile()
                bytes = b64decode(move_line.pdf_boleto_id.datas, validate=True)
                temp_pdf.write(bytes)
                temp_pdf.seek(0)
                pdf_merger.append(temp_pdf)
                temp_files.append(temp_pdf)

        temp_merged = tempfile.TemporaryFile()
        pdf_merger.write(temp_merged)
        pdf_merger.close()

        temp_merged.seek(0)
        datas = b64encode(temp_merged.read())

        self.pdf_boletos_id = self.env['ir.attachment'].create(
            {
                'name': (
                    "Boleto %s" % self.display_name.replace('/', '-')),
                'datas': datas,
                'datas_fname': ("boleto_%s.pdf" %
                                self.display_name.replace('/', '-')),
                'type': 'binary'
            }
        )

        for file in temp_files:
            file.close()

    def action_pdf_boleto(self):
        """
        Generates and lists all the attachment ids for an Boleto PDF of the
        invoice
        :return: actions.act_window
        """
        if not self.pdf_boletos_id:
            self._merge_pdf_boletos()

        boleto_id = self.pdf_boletos_id
        base_url = self.env['ir.config_parameter'].get_param(
            'web.base.url')
        download_url = '/web/content/%s/%s?download=True' % (
            str(boleto_id.id), boleto_id.name)

        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "new",
        }
