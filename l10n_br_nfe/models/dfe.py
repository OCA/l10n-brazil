# Copyright (C) 2025-Today - Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class DFe(models.Model):
    _inherit = "l10n_br_fiscal.dfe"

    def import_document(self):
        self.ensure_one()
        try:
            document = self.dfe_monitor_id._download_document(self.key)
            document_id = self.dfe_monitor_id._parse_xml_document(document)
        except Exception as e:
            self.message_post(
                body=_("Error importing document: \n\n %(error)s", error=e)
            )
            return
        if document_id:
            self.document_id = document_id

    def import_document_multi(self):
        for rec in self:
            rec.import_document()
