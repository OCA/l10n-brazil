# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants import MIT_SPECIAL_EVENT

# The layout accepts at most 5 special events in one assessment.
MIT_MAX_SPECIAL_EVENTS = 5


class DctfwebSpecialEvent(models.Model):
    """A termination, merger, spin-off or absorption inside the month.

    A special event cuts the month in two: the debits assessed up to its date
    point at it, and what happens afterwards goes to the after-event list.
    """

    _name = "l10n_br_dctfweb.special.event"
    _description = "DCTFWeb/MIT Special Event"
    _order = "assessment_id, day"

    assessment_id = fields.Many2one(
        comodel_name="l10n_br_dctfweb.assessment",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="assessment_id.company_id",
        store=True,
        readonly=True,
    )
    event_number = fields.Integer(
        compute="_compute_event_number",
        store=True,
        help="IdEvento: unique and sequential, from 1 to 5.",
    )
    day = fields.Integer(
        required=True,
        help="DiaEvento: the day of the month the event happened.",
    )
    event_type = fields.Selection(
        selection=MIT_SPECIAL_EVENT,
        required=True,
        help="TipoEvento.",
    )

    @api.depends("assessment_id.special_event_ids", "day")
    def _compute_event_number(self):
        for assessment in self.mapped("assessment_id"):
            events = assessment.special_event_ids.sorted("day")
            for number, event in enumerate(events, start=1):
                event.event_number = number
        for event in self.filtered(lambda e: not e.assessment_id):
            event.event_number = 0

    @api.constrains("day", "assessment_id")
    def _check_day(self):
        for record in self:
            assessment = record.assessment_id
            last_day = assessment.date_to and assessment.date_to.day or 31
            if not 1 <= record.day <= last_day:
                raise ValidationError(
                    _("The day of the special event must be between 1 and %s.")
                    % last_day
                )
            same_day = assessment.special_event_ids.filtered(
                lambda e, record=record: e.day == record.day and e != record
            )
            if same_day:
                raise ValidationError(
                    _("The layout does not accept two special events on the same day.")
                )
            if len(assessment.special_event_ids) > MIT_MAX_SPECIAL_EVENTS:
                raise ValidationError(
                    _("An assessment accepts at most %s special events.")
                    % MIT_MAX_SPECIAL_EVENTS
                )

    def _build_payload(self):
        self.ensure_one()
        return {
            "IdEvento": self.event_number,
            "DiaEvento": self.day,
            "TipoEvento": int(self.event_type),
        }
