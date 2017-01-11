# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields
from openerp.tests.common import TransactionCase
from openerp.addons.resource.tests import common


class TestResourceCalendar(common.TestResourceCommon):

    def setUp(self):
        super(TestResourceCalendar, self).setUp()

        self.resource_calendar = self.env['resource.calendar']
        self.resource_leaves = self.env['resource.calendar.leaves']

        # # Some date for demo
        # self.date3 = fields.Datetime.from_string('2016-10-04 10:11:12')
        # self.date4 = fields.Datetime.from_string('2016-10-07 10:11:12')

        # # Set as holiday a week after date3
        self.holiday_start = fields.Datetime.from_string('2016-10-11 00:00:00')
        self.holiday_end = fields.Datetime.from_string('2016-10-11 23:59:59')

    def test_00_add_leave(self):
        """ Inclusao de um novo Feriado """
        calendar = self.resource_calendar.browse(self.calendar_id)
        leave_ids = calendar.leave_ids
        self.leave_nacional_01 = self.resource_leaves.create({
            'name': 'Feriado Nacional 01',
            'date_from': self.holiday_start,
            'date_to': self.holiday_end,
            'calendar_id': calendar.id
        })
        self.assertEqual(len(leave_ids) + 1, len(calendar.leave_ids))

    def test_01_add_leave(self):
        pass
