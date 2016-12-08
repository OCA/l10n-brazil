# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields
from openerp.addons.resource.tests import common


class TestResourceCalendar(common.TestResourceCommon):

    def setUp(self):
        super(TestResourceCalendar, self).setUp()

        self.resource_calendar = self.env['resource.calendar']
        self.resource_leaves = self.env['resource.calendar.leaves']

        self.nacional_calendar_id = self.resource_calendar.create({
            'name': 'Calendario Nacional',
        })
        self.estadual_calendar_id = self.resource_calendar.create({
            'name': 'Calendario Nacional',
            'parent_id': self.nacional_calendar_id.id,
        })
        self.municipal_calendar_id = self.resource_calendar.create({
            'name': 'Calendario Nacional',
            'parent_id': self.estadual_calendar_id.id,
        })

    def test_00_add_leave_nacional(self):
        """ Inclusao de um novo Feriado no calendario nacional """
        leave_nacional_01 = self.resource_leaves.create({
            'name': 'Feriado Nacional 01',
            'date_from': fields.Datetime.from_string('2016-12-24 00:00:00'),
            'date_to': fields.Datetime.from_string('2016-12-24 23:59:59'),
            'calendar_id': self.nacional_calendar_id.id,
            'leave_type': 'F',
            'abrangencia': 'N',
        })
        self.assertEqual(leave_nacional_01.name, 'Feriado Nacional 01')
        self.assertEqual(leave_nacional_01.calendar_id,
                         self.nacional_calendar_id)
        self.assertEqual(1, len(self.nacional_calendar_id.leave_ids))

    def test_01_add_leave_estadual(self):
        """ Inclusao de um novo Feriado no calendario Estadual """
        leave_estadual_01 = self.resource_leaves.create({
            'name': 'Feriado Estadual 01',
            'date_from': fields.Datetime.from_string('2016-07-16 00:00:00'),
            'date_to': fields.Datetime.from_string('2016-07-16 23:59:59'),
            'calendar_id': self.estadual_calendar_id.id,
            'leave_type': 'F',
            'abrangencia': 'E',
        })
        self.assertEqual(leave_estadual_01.name, 'Feriado Estadual 01')
        self.assertEqual(leave_estadual_01.calendar_id,
                         self.estadual_calendar_id)
        self.assertEqual(1, len(self.estadual_calendar_id.leave_ids))

    def test_01_add_leave_municipal(self):
        """ Inclusao de um novo Feriado no calendario municipal """
        leave_municipal_01 = self.resource_leaves.create({
            'name': 'Feriado Municipal 01',
            'date_from': fields.Datetime.from_string('2016-03-10 00:00:00'),
            'date_to': fields.Datetime.from_string('2016-03-10 23:59:59'),
            'calendar_id': self.municipal_calendar_id.id,
            'leave_type': 'F',
            'abrangencia': 'E',
        })
        self.assertEqual(leave_municipal_01.name, 'Feriado Municipal 01')
        self.assertEqual(leave_municipal_01.calendar_id,
                         self.municipal_calendar_id)
        self.assertEqual(1, len(self.municipal_calendar_id.leave_ids))
