# Copyright 2023 Akretion (Raphaẽl Valyi <raphael.valyi@akretion.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def create_document_from_attachment(self, attachment_ids=None):
        if self.env.company.country_id.code != "BR" or len(attachment_ids) < 1:
            return super().create_document_from_attachment(
                attachment_ids=attachment_ids
            )
        attachments = self.env["ir.attachment"].browse(attachment_ids)
        return self.env[
            "l10n_br_fiscal.document.import.wizard.mixin"
        ]._get_importer_action(attachments)
