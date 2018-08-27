# -*- coding: utf-8 -*-
# @ 2017 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class ResConfig(models.TransientModel):
    _inherit = 'account.config.settings'

    date_used_maturity = fields.Selection(
        related='company_id.date_used_maturity'
    )
