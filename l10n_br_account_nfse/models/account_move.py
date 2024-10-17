# Copyright (C) 2023 Antônio S. P. Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class AccountMove(models.Model):

    _inherit = "account.move"

    def action_open_nfse(self):
        self.ensure_one()
        return self.fiscal_document_id.action_open_nfse()
