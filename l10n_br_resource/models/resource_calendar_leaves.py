# Copyright 2016 KMEE - Luis Felipe Miléo <mileo@kmee.com.br>
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

HOLIDAY_TYPE_LABELS = [
    ("F", "Feriado"),
    ("B", "Feriado bancário"),
    ("C", "Data comemorativa"),
]


HOLIDAY_COVERAGE_LABELS = [
    ("N", "Nacional"),
    ("E", "Estadual"),
    ("M", "Municipal"),
]


class ResourceCalendarLeave(models.Model):
    _inherit = "resource.calendar.leaves"

    country_id = fields.Many2one(
        "res.country",
        string="Country",
        related="calendar_id.country_id",
    )
    state_id = fields.Many2one(
        "res.country.state",
        "State",
        related="calendar_id.state_id",
        domain="[('country_id','=',country_id)]",
    )
    l10n_br_city_id = fields.Many2one(
        "res.city",
        "Municipality",
        related="calendar_id.l10n_br_city_id",
        domain="[('state_id','=',state_id)]",
    )
    leave_type = fields.Selection(
        string="Type",
        selection=HOLIDAY_TYPE_LABELS,
    )
    coverage = fields.Selection(
        selection=HOLIDAY_COVERAGE_LABELS,
    )
