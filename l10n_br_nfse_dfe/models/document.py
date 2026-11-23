# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from io import BytesIO

from brazilfiscalreport.danfse import Danfse

from odoo import models


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def make_pdf(self):
        """The DANFSE of a national NFS-e that was imported is printed from the
        original XML that the import attached, which is neither regenerated nor
        changed; the PDF is kept on the document."""
        imported = self.filtered(
            lambda doc: doc.imported_document
            and doc.original_xml_file_id
            and doc._is_national_nfse_key()
        )
        for document in imported:
            buffer = BytesIO()
            Danfse(xml=document.original_xml_file_id.raw).output(buffer)
            vals = {
                "name": f"DANFSE_{document.document_key}.pdf",
                "res_model": document._name,
                "res_id": document.id,
                "datas": base64.b64encode(buffer.getvalue()),
                "mimetype": "application/pdf",
                "type": "binary",
            }
            if document.file_report_id:
                document.file_report_id.write(vals)
            else:
                document.file_report_id = self.env["ir.attachment"].create(vals)
        return super(Document, self - imported).make_pdf()
