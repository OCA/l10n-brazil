# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class ResourceCalendar(models.Model):

    _inherit = 'resource.calendar'

    parent_id = fields.Many2one(
        'resource.calendar',
        string='Parent Calendar',
        ondelete='restrict',
        index=True)
    child_ids = fields.One2many(
        'resource.calendar', 'parent_id',
        string='Child Calendar')
    _parent_store = True
    parent_left = fields.Integer(index=True)
    parent_right = fields.Integer(index=True)

    @api.constrains('parent_id')
    def _check_hierarchy(self):
        if not self._check_recursion():
            raise models.ValidationError(
                'Error! You cannot create recursive calendars.')
