# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _, api, models
from odoo.exceptions import Warning as UserError


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    # TODO REMOVE THIS FILE
