# -*- coding: utf-8 -*-
#    Copyright (C) 2015 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Miléo (mileo@kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class ResConfig(models.Model):
    _inherit = 'account.config.settings'

    ipbt_token = fields.Char(
        string='IPBT Token',
        related='company_id.ipbt_token'
    )
