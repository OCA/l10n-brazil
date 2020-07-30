# @ 2020 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    import_type = fields.Selection(
        selection_add=[('cnab400', 'CNAB 400'), ('cnab240', 'CNAB 240')]
    )
