# -*- coding: utf-8 -*-
# Copyright (C) 2017 - Daniel Sadamo - KMEE INFORMATICA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    use_move_template_accounting= fields.Boolean(
        string=u'Utilizar roteiros contábeis',
        related='company_id.use_moves_line_templates'
    )
