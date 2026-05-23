# Copyright 2016 KMEE - Luis Felipe Miléo <mileo@kmee.com.br>
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"
    _parent_store = True

    def _compute_recursive_leaves(self, calendar):
        res = self.env["resource.calendar.leaves"]
        res |= self.env["resource.calendar.leaves"].search(
            [("calendar_id", "=", calendar.id)]
        )
        if calendar.parent_id:
            res |= self._compute_recursive_leaves(calendar.parent_id)
        return res

    @api.depends("parent_id")
    def _compute_leave_ids(self):
        for calendar in self:
            calendar.leave_ids = self._compute_recursive_leaves(calendar)

    parent_id = fields.Many2one(
        "resource.calendar", string="Parent Calendar", ondelete="restrict", index=True
    )
    child_ids = fields.One2many(
        "resource.calendar", "parent_id", string="Child Calendar"
    )

    parent_path = fields.Char(index=True)

    country_id = fields.Many2one("res.country", "Country")
    state_id = fields.Many2one(
        "res.country.state", "State", domain="[('country_id','=',country_id)]"
    )
    l10n_br_city_id = fields.Many2one(
        "res.city", "Municipality", domain="[('state_id','=',state_id)]"
    )
    leave_ids = fields.Many2many(
        comodel_name="resource.calendar.leaves", compute="_compute_leave_ids"
    )

    @api.constrains("parent_id")
    def _check_hierarchy(self):
        if self._has_cycle():
            raise ValidationError(
                self.env._("Error! You cannot create recursive hierarchies.")
            )

    def get_leave_intervals(
        self, resource_id=None, start_datetime=None, end_datetime=None
    ):
        """Get the leaves of the calendar. Leaves can be filtered on the
        resource, the start datetime or the end datetime.

        :param int resource_id: the id of the resource to take into account
                                when computing the leaves. If not set,
                                only general leaves are computed.
                                If set, generic and specific leaves
                                are computed.
        :param datetime start_datetime: if provided, do not take into
                                        account leaves ending before
                                        this date.
        :param datetime end_datetime: if provided, do not take into
                                        account leaves beginning
                                        after this date.

        :return list leaves: list of tuples (start_datetime, end_datetime) of
                             leave intervals
        """
        leaves = []
        for leave in self.leave_ids:
            if leave.resource_id and resource_id:
                if not resource_id == leave.resource_id.id:
                    continue
            elif leave.resource_id and not resource_id:
                continue
            date_from = leave.date_from
            if end_datetime and date_from > end_datetime:
                continue
            date_to = leave.date_to
            if start_datetime and date_to < start_datetime:
                continue
            leaves.append(leave)
        return leaves

    def is_holiday(self, date):
        """Check if a date is a holiday.

        :param datetime date: date to check. If not provided, checks today.
        :return boolean: True if the date is a holiday, False otherwise.
        """
        if not date:
            date = datetime.now()
        for leave in self.leave_ids:
            if leave.date_from <= date:
                if leave.date_to >= date:
                    if leave.leave_type == "F":
                        return True
        return False

    def is_bank_holiday(self, reference_date):
        """Check if a date is a bank holiday.

        :param datetime reference_date: date to check. If not provided,
                                        checks today.
        :return int: number of matching bank holiday leaves (> 0 if it is
                     a bank holiday, 0 otherwise).
        """
        if not reference_date:
            reference_date = datetime.now()
        domain = [
            ("date_from", "<=", reference_date.strftime("%Y-%m-%d %H:%M:%S")),
            ("date_to", ">=", reference_date.strftime("%Y-%m-%d %H:%M:%S")),
            ("leave_type", "in", ["F", "B"]),
        ]
        leaves_count = self.env["resource.calendar.leaves"].search_count(domain)
        return leaves_count

    def is_extended_holiday(self, reference_date):
        """Check if a date is a bridged/extended holiday (feriado emendado).

        A day is considered bridged when it falls between a holiday and a weekend.

        :param datetime reference_date: date to check. If not provided,
                                        checks today.
        :return boolean: True if the date is a bridged holiday, False otherwise.
        """
        if not reference_date:
            reference_date = datetime.now()
        is_holiday_result = self.is_holiday(reference_date)
        day_before = reference_date - timedelta(days=1)
        day_after = reference_date + timedelta(days=1)

        day_before_is_monday = (
            True if day_before.weekday() == 0 or self.is_holiday(day_before) else False
        )
        day_after_is_friday = (
            True if day_after.weekday() == 4 or self.is_holiday(day_after) else False
        )

        return is_holiday_result and (day_before_is_monday or day_after_is_friday)

    def is_business_day(self, date):
        """Check if a date is a business day.

        :param datetime date: date to check. If not provided, checks today.
        :return boolean: True if it is a business day, False otherwise.
        """
        if not date:
            date = datetime.now()
        return not self.is_holiday(date) and date.weekday() <= 4 or False

    def count_business_days(self, start_date, end_date):
        """Count the number of business days in a given period.

        :param datetime start_date: start of the period.
        :param datetime end_date: end of the period.
        :return int: number of business days.
        """
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = datetime.now()
        business_days = 0
        while start_date <= end_date:
            if self.is_business_day(start_date):
                business_days += 1
            start_date += timedelta(days=1)

        return business_days

    def next_business_day(self, reference_date):
        """Return the next business day after reference_date.

        :param datetime reference_date: reference date. If not provided,
                                        checks tomorrow.
        :return datetime: next business day from reference_date.
        """
        if not reference_date:
            reference_date = datetime.now()
        reference_date += timedelta(days=1)
        while reference_date:
            if self.is_business_day(reference_date):
                return reference_date
            reference_date += timedelta(days=1)

    def get_base_days(self, date_from, date_to, commercial_month=True):
        """Calculate the number of payable days in a given time interval.

        :param datetime date_from: start date of the interval.
        :param datetime date_to: end date of the interval.
        :param bool commercial_month: if True, uses 30-day commercial month.
        :return int: number of payable days.
        """
        if not date_from:
            date_from = datetime.now()
        if not date_to:
            date_to = datetime.now()
        # Commercial month is always 30 days
        if commercial_month:
            return 30 - date_from.day + 1
        # On hire/termination, do not use commercial month
        days_count = (date_to - date_from).days + 1
        if days_count > 30:
            return 30
        else:
            return days_count

    def is_bank_business_day(self, date):
        """Check if a date is a bank business day.

        :param datetime date: date to check. If not provided, checks today.
        :return boolean: True if it is a bank business day, False otherwise.
        """
        if not date:
            date = datetime.now()
        if date.weekday() >= 5:
            return False
        elif self.is_bank_holiday(date):
            return False
        return True

    def next_bank_business_day(self, reference_date):
        """Return the next bank business day after reference_date.

        :param datetime reference_date: reference date. If not provided,
                                        checks tomorrow.
        :return datetime: next bank business day from reference_date.
        """
        if not reference_date:
            reference_date = datetime.now()
        reference_date += timedelta(days=1)
        if self.is_bank_business_day(reference_date):
            return reference_date
        return self.next_bank_business_day(reference_date)
