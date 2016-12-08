# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from openerp import api, fields, models, _

_logger = logging.getLogger(__name__)

try:
    from pybrasil.feriado.constantes import (
        TIPO_FERIADO, ABRANGENCIA_FERIADO,
    )
except ImportError:
    _logger.info('Cannot import pybrasil')


class ResourceCalendar(models.Model):

    _inherit = 'resource.calendar'

    def _compute_recursive_leaves(self, calendar):
        res = self.env['resource.calendar.leaves']
        res |= self.env['resource.calendar.leaves'].search([
            ('calendar_id', '=', calendar.id)
        ])
        if calendar.parent_id:
            res |= self._compute_recursive_leaves(calendar.parent_id)
        return res

    @api.multi
    @api.depends('parent_id')
    def _compute_leave_ids(self):
        for calendar in self:
            calendar.leave_ids = self._compute_recursive_leaves(calendar)

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

    country_id = fields.Many2one('res.country', u'País')
    state_id = fields.Many2one(
        'res.country.state', u'Estado',
        domain="[('country_id','=',country_id)]")
    l10n_br_city_id = fields.Many2one(
        'l10n_br_base.city', u'Municipio',
        domain="[('state_id','=',state_id)]")
    leave_ids = fields.Many2many(
        comodel_name='resource.calendar.leaves',
        compute='_compute_leave_ids'
    )

    @api.constrains('parent_id')
    def _check_hierarchy(self):
        if not self._check_recursion():
            raise models.ValidationError(_(
                'Error! You cannot create recursive calendars.'))


class ResourceCalendarLeave(models.Model):

    _inherit = 'resource.calendar.leaves'

    country_id = fields.Many2one(
        'res.country', string=u'País',
        related='calendar_id.country_id',
    )
    state_id = fields.Many2one(
        'res.country.state', u'Estado',
        related='calendar_id.state_id',
        domain="[('country_id','=',country_id)]",
        readonly=True
    )
    l10n_br_city_id = fields.Many2one(
        'l10n_br_base.city', u'Municipio',
        related='calendar_id.l10n_br_city_id',
        domain="[('state_id','=',state_id)]",
        readonly=True
    )
    leave_type = fields.Selection(
        string=u'Tipo',
        selection=[item for item in TIPO_FERIADO.iteritems()],
    )
    abrangencia = fields.Selection(
        string=u'Abrangencia',
        selection=[item for item in ABRANGENCIA_FERIADO.iteritems()],
    )
