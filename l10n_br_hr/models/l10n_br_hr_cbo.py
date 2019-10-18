# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class L10nBrHrCbo(models.Model):
    _name = "l10n_br_hr.cbo"
    _inherit = "l10n_br_hr.data.abstract"
    _description = "Brazilian Classification of Occupation"
