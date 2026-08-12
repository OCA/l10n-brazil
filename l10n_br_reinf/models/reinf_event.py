# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64
import logging
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..constants import (
    REINF_ENVIRONMENTS,
    REINF_EVENT_GROUP_CLOSING,
    REINF_EVENT_GROUPS,
    REINF_EVENT_STATES,
    REINF_EVENT_TYPE_GROUP,
    REINF_EVENT_TYPES,
    REINF_INSCRIPTION_TYPES,
    REINF_RECTIFY_INDICATORS,
    REINF_RECTIFY_ORIGINAL,
    REINF_RECTIFY_RECTIFICATION,
)
from ..tools.reinf_id import ReinfIdError, build_event_id, validate_event_id
from ..tools.reinf_schema import validate_event_xml

_logger = logging.getLogger(__name__)

EVENT_SEQUENCE_CODE = "l10n_br_reinf.event"
PERIOD_RE = re.compile(r"^\d{4}(-(0[1-9]|1[0-2]))?$")


class ReinfEvent(models.Model):
    """An EFD-Reinf event, from the draft to the receipt of the tax authority.

    The field names mirror l10n_br_fiscal.event of l10n_br_fiscal_edi, so that
    whoever already reads a fiscal event reads this one: the XML of the request
    and of the answer live in ir.attachment (file_request_id and
    file_response_id), the answer of the web service lives in status_code /
    response / message, and the batch identifiers live in protocol_number and
    lot_receipt_number.

    What the EFD-Reinf adds to that model is the identifier of the event
    (36 positions, built here), the period of the event, the rectification
    chain and the polymorphic origin, because a Reinf event is not born from a
    fiscal document: it is born from a payment, from a closing or from the
    company registration itself.
    """

    _name = "l10n_br_reinf.event"
    _inherit = ["mail.thread"]
    _description = "EFD-Reinf Event"
    _order = "period desc, event_type, id desc"
    _rec_name = "event_key"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )

    event_type = fields.Selection(
        selection=REINF_EVENT_TYPES,
        string="Event",
        required=True,
        index=True,
        tracking=True,
    )

    event_group = fields.Selection(
        selection=REINF_EVENT_GROUPS,
        compute="_compute_event_group",
        store=True,
        index=True,
        help="Functional group of the event. A batch only carries events of a "
        "single group.",
    )

    event_key = fields.Char(
        string="Event Id",
        size=36,
        index=True,
        copy=False,
        readonly=True,
        tracking=True,
        help="The id attribute of the event: ID, the type and the number of the "
        "inscription of the taxpayer, the moment of the generation and a "
        "sequential, in 36 positions.",
    )

    sequence = fields.Char(
        string="Sequential",
        copy=False,
        readonly=True,
        help="The 5 last positions of the event id.",
    )

    period = fields.Char(
        size=7,
        index=True,
        tracking=True,
        help="perApur of the event, as AAAA-MM, or AAAA for the events whose "
        "period is a year.",
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Beneficiary",
        index=True,
        help="Beneficiary of the payment the event declares, when the event has "
        "a single one.",
    )

    inscription_type = fields.Selection(
        selection=REINF_INSCRIPTION_TYPES,
        readonly=True,
        copy=False,
        help="tpInsc used to build the event id.",
    )

    inscription = fields.Char(
        readonly=True,
        copy=False,
        help="nrInsc used to build the event id.",
    )

    # Polymorphic origin. A Reinf event does not descend from a fiscal
    # document: it can be born from an account.move, from an
    # account.move.line, from a closing or from res.company itself. Instead of
    # one many2one per possible source, the source is kept as a model plus an
    # id, the way ir.attachment and mail.message do.
    origin_model = fields.Char(
        string="Source Model",
        readonly=True,
        index=True,
    )

    origin_id = fields.Integer(
        string="Source Id",
        readonly=True,
        index=True,
    )

    origin = fields.Char(
        string="Source Document",
        readonly=True,
        help="Human readable reference of what generated this event.",
    )

    state = fields.Selection(
        selection=REINF_EVENT_STATES,
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
        help="tpAmb the event was transmitted with.",
    )

    batch_id = fields.Many2one(
        comodel_name="l10n_br_reinf.batch",
        string="Batch",
        index=True,
        readonly=True,
        copy=False,
        ondelete="set null",
    )

    rectify_indicator = fields.Selection(
        selection=REINF_RECTIFY_INDICATORS,
        string="Rectification",
        default=REINF_RECTIFY_ORIGINAL,
        required=True,
        help="indRetif of the event.",
    )

    rectified_event_id = fields.Many2one(
        comodel_name="l10n_br_reinf.event",
        string="Rectified Event",
        readonly=True,
        copy=False,
        help="The event this one rectifies.",
    )

    rectification_ids = fields.One2many(
        comodel_name="l10n_br_reinf.event",
        inverse_name="rectified_event_id",
        string="Rectifications",
    )

    receipt_number = fields.Char(
        readonly=True,
        copy=False,
        tracking=True,
        help="nrRecibo returned by the tax authority. It is what a "
        "rectification and an exclusion point to.",
    )

    receipt_date = fields.Datetime(
        readonly=True,
        copy=False,
    )

    protocol_number = fields.Char(
        readonly=True,
        copy=False,
    )

    protocol_date = fields.Datetime(
        readonly=True,
        copy=False,
        index=True,
    )

    lot_receipt_number = fields.Char(
        string="Batch Receipt Number",
        readonly=True,
        copy=False,
        help="In asynchronous processing, a batch receipt number is generated, "
        "which is used for later consultation.",
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

    message = fields.Char(
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

    occurrence_ids = fields.One2many(
        comodel_name="l10n_br_reinf.occurrence",
        inverse_name="event_id",
        string="Occurrences",
        readonly=True,
    )

    # The R-1000 is the one event that is persisted as a record of its own,
    # because it is a versioned declaration. The others are serialized straight
    # from what generated them, by _serialize_<code>.
    r1000_id = fields.Many2one(
        comodel_name="l10n_br_reinf.r1000",
        string="R-1000 Detail",
        readonly=True,
        copy=False,
        ondelete="set null",
    )

    _sql_constraints = [
        (
            "reinf_event_key_uniq",
            "unique (event_key)",
            "The id of an EFD-Reinf event must be unique.",
        )
    ]

    @api.depends("event_type")
    def _compute_event_group(self):
        for record in self:
            record.event_group = REINF_EVENT_TYPE_GROUP.get(record.event_type)

    @api.constrains("event_key")
    def _check_event_key(self):
        for record in self.filtered("event_key"):
            try:
                validate_event_id(record.event_key)
            except ReinfIdError as error:
                raise ValidationError(str(error)) from error

    @api.constrains("period")
    def _check_period(self):
        for record in self.filtered("period"):
            if not PERIOD_RE.match(record.period):
                raise ValidationError(
                    _(
                        "The period %(period)s is not valid: write it as AAAA-MM, "
                        "or as AAAA for the events whose period is a year.",
                        period=record.period,
                    )
                )

    def _next_event_sequence(self):
        """Return the sequential of the event id.

        The 5 positions of the sequential only have to keep the id unique
        inside the same second, so the sequence wraps around instead of
        overflowing the field.
        """
        number = self.env["ir.sequence"].next_by_code(EVENT_SEQUENCE_CODE)
        if not number:
            raise UserError(
                _(
                    "The sequence %s is missing. Reinstall or update the "
                    "l10n_br_reinf module to restore it.",
                    EVENT_SEQUENCE_CODE,
                )
            )
        return int(re.sub(r"\D", "", number) or 0)

    def _build_event_key(self, moment=None):
        """Build the id of the event without writing it."""
        self.ensure_one()
        inscription_type, inscription = self.company_id._reinf_inscription()
        sequence = self._next_event_sequence()
        try:
            event_key = build_event_id(
                inscription_type,
                inscription,
                moment or fields.Datetime.now(),
                sequence,
            )
        except ReinfIdError as error:
            raise UserError(str(error)) from error
        return event_key, inscription_type, inscription, sequence

    def _ensure_event_key(self):
        """Write the id of the event, once, keeping it stable afterwards."""
        for record in self.filtered(lambda event: not event.event_key):
            (
                event_key,
                inscription_type,
                inscription,
                sequence,
            ) = record._build_event_key()
            record.write(
                {
                    "event_key": event_key,
                    "inscription_type": inscription_type,
                    "inscription": inscription,
                    "sequence": str(sequence).zfill(5),
                }
            )
        return True

    def _save_event_file(self, xml, response=False):
        """Store an XML of the event as an attachment of the event itself.

        The attachment is attached to the event so that it inherits its access
        rules: an EFD-Reinf event carries the CPF, the name and the amounts
        paid to a beneficiary, and that is personal data.
        """
        self.ensure_one()
        suffix = "ret" if response else "env"
        attachment = self.env["ir.attachment"].create(
            {
                "name": f"{self.event_key or self.event_type}-{suffix}.xml",
                "res_model": self._name,
                "res_id": self.id,
                "datas": base64.b64encode(xml.encode("utf-8")),
                "mimetype": "application/xml",
                "type": "binary",
            }
        )
        if response:
            self.file_response_id = attachment
        else:
            self.file_request_id = attachment
        return attachment

    def _serialize_method(self):
        """Name of the method that serializes this type of event.

        Dynamic dispatch, the same way spec_export dispatches on the class
        name: every event of the layout has its own structure, so adding an
        event is adding a _serialize_<code> method and nothing else.
        """
        self.ensure_one()
        return "_serialize_%s" % (self.event_type or "").replace("-", "").lower()

    def _serialize_r1000(self):
        """The R-1000 is persisted as a record, so it serializes itself."""
        self.ensure_one()
        if not self.r1000_id:
            raise NotImplementedError(
                _("The event %s has no R-1000 detail record.", self.display_name)
            )
        return self.r1000_id._build_event_xml()

    def _serialize(self):
        """Return the XML of the event, unsigned.

        The signature is applied later, by the transmission, which is where the
        certificate is.
        """
        self.ensure_one()
        method = self._serialize_method()
        if not hasattr(self, method):
            raise NotImplementedError(
                _(
                    "Events of type %s are not implemented yet.",
                    self.event_type,
                )
            )
        return getattr(self, method)()

    def _xsd_errors(self, xml, ignore_signature=True):
        """Validate an XML of this event against the official XSD."""
        self.ensure_one()
        return validate_event_xml(xml, self.event_type, ignore_signature)

    def action_generate_xml(self):
        """Serialize the event, check it against the XSD and store it."""
        for record in self:
            xml = record._serialize()
            errors = record._xsd_errors(xml)
            if errors:
                raise UserError(
                    _(
                        "The XML of the event %(event)s does not match the "
                        "layout:\n%(errors)s",
                        event=record.display_name,
                        errors="\n".join(errors),
                    )
                )
            record._save_event_file(xml)
        return True

    def action_validate(self):
        """Move a draft event to validated, giving it its id."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    _(
                        "Only a draft event can be validated, and %s is not " "draft.",
                        record.display_name,
                    )
                )
            record._ensure_event_key()
            record.state = "validated"
        return True

    def action_set_draft(self):
        """Send an event back to draft, keeping its id.

        The id is kept on purpose: it was never transmitted, and rebuilding it
        would only burn a sequential.
        """
        for record in self:
            if record.state not in ("validated", "pending", "rejected"):
                raise UserError(
                    _(
                        "The event %s cannot go back to draft from the status "
                        "it is in.",
                        record.display_name,
                    )
                )
            record.state = "draft"
        return True

    def action_rectify(self):
        """Create the rectifying event of an accepted event.

        The rectification is a new event pointing at the receipt of the old
        one, never an edition of what was already accepted.
        """
        rectifications = self.env[self._name]
        for record in self:
            if record.state != "accepted" or not record.receipt_number:
                raise UserError(
                    _(
                        "Only an accepted event with a receipt number can be "
                        "rectified, and %s is not one.",
                        record.display_name,
                    )
                )
            rectification = record.copy(
                {
                    "rectify_indicator": REINF_RECTIFY_RECTIFICATION,
                    "rectified_event_id": record.id,
                    "state": "draft",
                }
            )
            record.state = "rectified"
            rectifications |= rectification
        return rectifications

    def _register_response(
        self,
        state,
        status_code=None,
        response=None,
        receipt_number=None,
        occurrences=None,
    ):
        """Write the answer of the tax authority on the event.

        The payload is deliberately never logged: it carries personal data.
        """
        self.ensure_one()
        values = {"state": state}
        if status_code is not None:
            values["status_code"] = status_code
        if response is not None:
            values["response"] = response
        if receipt_number is not None:
            values["receipt_number"] = receipt_number
            values["receipt_date"] = fields.Datetime.now()
        self.write(values)
        for occurrence in occurrences or []:
            self.env["l10n_br_reinf.occurrence"].create(
                dict(occurrence, event_id=self.id)
            )
        _logger.info(
            "EFD-Reinf event %s of company %s answered as %s",
            self.event_key,
            self.company_id.id,
            state,
        )
        return True

    def _is_closing(self):
        self.ensure_one()
        return self.event_group == REINF_EVENT_GROUP_CLOSING
