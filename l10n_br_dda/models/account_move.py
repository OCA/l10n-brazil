# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from ..constants import DEBIT_MODEL


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        self.env[DEBIT_MODEL].sudo()._dda_on_bill_posted(posted)
        return posted
