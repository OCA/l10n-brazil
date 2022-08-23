# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models


class AccountJournal(models.Model):

    _inherit = "account.journal"

    used_to_import_cnab = fields.Boolean(string="Journal used for import CNAB")
