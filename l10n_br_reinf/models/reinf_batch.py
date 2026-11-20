# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..constants import (
    REINF_BATCH_MAX_EVENTS,
    REINF_BATCH_STATES,
    REINF_ENVIRONMENTS,
    REINF_EVENT_GROUP_CLOSING,
    REINF_EVENT_GROUPS,
)

_logger = logging.getLogger(__name__)

BATCH_SEQUENCE_CODE = "l10n_br_reinf.batch"


class ReinfBatch(models.Model):
    """A batch of events sent to the asynchronous reception service.

    The rules of the batch are not a matter of taste. The tax authority
    processes the events of a batch in parallel, with no guaranteed order, so a
    closing event can never travel with the periodic events it is supposed to
    close. On top of that the envelope of the layout accepts at most 50 events,
    and the batch has to be homogeneous.

    Nothing is transmitted at this stage: _transport_send and _transport_query
    are the only two doors to the web services, and they are declared here so
    the rest of the module can be written and tested against a mock before the
    REST transport exists.
    """

    _name = "l10n_br_reinf.batch"
    _inherit = ["mail.thread"]
    _description = "EFD-Reinf Event Batch"
    _order = "id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default="/",
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )

    state = fields.Selection(
        selection=REINF_BATCH_STATES,
        string="Status",
        default="draft",
        required=True,
        index=True,
        readonly=True,
        copy=False,
        tracking=True,
    )

    environment = fields.Selection(
        selection=REINF_ENVIRONMENTS,
        readonly=True,
        copy=False,
    )

    event_ids = fields.One2many(
        comodel_name="l10n_br_reinf.event",
        inverse_name="batch_id",
        string="Events",
    )

    # No string here on purpose: the default label of the field is already
    # "Event Count", which is what keeps it from clashing with the label of
    # event_ids. A duplicated label raises a WARNING at loading, and the OCA
    # checklog fails the build on any warning.
    event_count = fields.Integer(
        compute="_compute_event_count",
        store=True,
    )

    event_group = fields.Selection(
        selection=REINF_EVENT_GROUPS,
        compute="_compute_event_count",
        store=True,
        help="All the events of a batch belong to the same group.",
    )

    protocol_number = fields.Char(
        readonly=True,
        copy=False,
        index=True,
        help="nrProtLote returned by the reception of the batch. It is what the "
        "later query asks about.",
    )

    protocol_date = fields.Datetime(
        readonly=True,
        copy=False,
    )

    file_request_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML",
        readonly=True,
        copy=False,
    )

    file_response_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML Response",
        readonly=True,
        copy=False,
    )

    status_code = fields.Char(
        readonly=True,
        copy=False,
    )

    response = fields.Char(
        string="Response Message",
        readonly=True,
        copy=False,
    )

    occurrence_ids = fields.One2many(
        comodel_name="l10n_br_reinf.occurrence",
        inverse_name="batch_id",
        string="Occurrences",
        readonly=True,
    )

    @api.depends("event_ids", "event_ids.event_group")
    def _compute_event_count(self):
        for record in self:
            record.event_count = len(record.event_ids)
            groups = set(record.event_ids.mapped("event_group"))
            record.event_group = groups.pop() if len(groups) == 1 else False

    @api.constrains("event_ids")
    def _check_events(self):
        for record in self:
            events = record.event_ids
            if not events:
                continue
            if len(events) > REINF_BATCH_MAX_EVENTS:
                raise ValidationError(
                    _(
                        "A batch carries at most %(maximum)s events, and this one "
                        "has %(count)s. Split it.",
                        maximum=REINF_BATCH_MAX_EVENTS,
                        count=len(events),
                    )
                )
            if len(set(events.mapped("event_group"))) > 1:
                raise ValidationError(
                    _(
                        "A batch only carries events of a single group. This one "
                        "mixes %s.",
                        ", ".join(sorted(set(events.mapped("event_group")))),
                    )
                )
            if any(event._is_closing() for event in events) and len(events) > 1:
                # A closing event travels alone: the tax authority processes the
                # events of a batch in parallel, so a closing sent along with
                # the events it closes may be processed before them.
                raise ValidationError(
                    _(
                        "A closing or reopening event travels alone in its own "
                        "batch, never with the events it closes."
                    )
                )
            if len(set(events.mapped("company_id"))) > 1:
                raise ValidationError(
                    _("All the events of a batch belong to the same company.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code(BATCH_SEQUENCE_CODE) or "/"
                )
        return super().create(vals_list)

    def _transport_send(self):
        """Send the batch to the asynchronous reception service.

        The only door out of Odoo for a batch. It has to answer the protocol
        number of the batch, and it is replaced by a mock in the tests.

        :return: the protocol number (nrProtLote) of the batch.
        """
        raise NotImplementedError(
            _(
                "The EFD-Reinf REST transport is not implemented yet. Install the "
                "transport of the EFD-Reinf to send a batch."
            )
        )

    def _transport_query(self):
        """Query the processing of the batch by its protocol number.

        The counterpart of _transport_send, called by the polling. It has to
        answer the result of every event of the batch, and it is replaced by a
        mock in the tests.
        """
        raise NotImplementedError(
            _(
                "The EFD-Reinf REST transport is not implemented yet. Install the "
                "transport of the EFD-Reinf to query a batch."
            )
        )

    def action_send(self):
        """Check the batch and hand it over to the transport."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    _("Only a draft batch can be sent, and %s is not draft.")
                    % record.display_name
                )
            if not record.event_ids:
                raise UserError(
                    _("The batch %s has no event to send.") % record.display_name
                )
            environment = record.company_id._reinf_environment()
            pending = record.event_ids.filtered(
                lambda event: event.state not in ("validated", "pending")
            )
            if pending:
                raise UserError(
                    _(
                        "Every event of a batch is validated before the batch is "
                        "sent. %s is not.",
                        ", ".join(pending.mapped("display_name")),
                    )
                )
            record.event_ids._ensure_event_key()
            record.environment = environment
            record.event_ids.write({"environment": environment})
            record.protocol_number = record._transport_send()
            record.state = "sent"
        return True

    def _is_closing(self):
        self.ensure_one()
        return self.event_group == REINF_EVENT_GROUP_CLOSING
