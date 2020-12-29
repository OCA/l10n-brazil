# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountJournal(models.Model):

    _inherit = 'account.journal'

    bank_inter_cert = fields.Binary(string='Bank Inter Certificate')

    bank_inter_key = fields.Binary(string='Bank Inter Key')
