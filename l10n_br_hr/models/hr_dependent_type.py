# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class HrDependentType(models.Model):
    _name = "hr.dependent.type"
    _inherit = "l10n_br_hr.data.abstract"
    _description = "Dependents Type"
