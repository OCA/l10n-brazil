# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class HrJob(models.Model):
    _inherit = 'hr.job'

    cbo_id = fields.Many2one('l10n_br_hr.cbo', 'CBO')
