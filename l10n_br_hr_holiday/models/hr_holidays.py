# -*- coding: utf-8 -*-
# Copyright 2016 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class HrHolidays(models.Model):

    _inherit = 'hr.holidays'

    message = fields.Char(
        string=u"Mensagem",
        related='holiday_status_id.message',
    )
