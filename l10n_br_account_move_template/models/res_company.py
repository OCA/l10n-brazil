# -*- coding: utf-8 -*-
# Copyright (C) 2017 - Daniel Sadamo - KMEE INFORMATICA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    use_move_line_templates = fields.Boolean(
        string=u'Utilizar roteiros contábeis'
    )
