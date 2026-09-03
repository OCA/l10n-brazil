# Copyright (C) 2019  Renato Lima - Akretion
# Copyright (C) 2019  KMEE INFORMATICA LTDA
# Copyright (C) 2026  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base.fiscal.edoc import ChaveEdoc
from transitions import Machine, MachineError

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER,
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_STATE_CANCEL,
    DOCUMENT_STATE_DRAFT,
    DOCUMENT_STATE_INVALIDATED,
    DOCUMENT_STATE_OPEN,
    MODELO_FISCAL_CTE,
    MODELO_FISCAL_MDFE,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFSE,
    PROCESSADOR_NENHUM,
    SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO,
)

from ..constants.fiscal import (
    DOCUMENT_STATE_AUTHORIZED,
    DOCUMENT_STATE_DENIED,
    DOCUMENT_STATE_REJECTED,
    DOCUMENT_STATE_SENDING,
    DOCUMENT_STATES,
)


def filter_processador(record):
    if record.document_electronic and record.processador_edoc == PROCESSADOR_NENHUM:
        return True
    return False


class FiscalDocumentStateMachine(Machine):
    """A ``transitions`` Machine bound to an Odoo fiscal document.

    Odoo recordsets are slotted (``__slots__ = env/_ids/_prefetch_ids``), so
    the machine cannot be attached to the record itself the way ``transitions``
    normally expects (it sets trigger methods on its model).  Instead the
    machine keeps its own state (its model is itself) and writes every state
    change back to the document synchronously in ``set_state()``, which
    ``transitions`` calls *before* running the transition ``after`` callbacks.
    Nested ``_trigger_fsm()`` calls made from those callbacks (e.g. the
    send -> authorize chain) therefore always read the up-to-date state_edoc.
    The initial ``set_state()`` done at machine construction is a no-op write
    thanks to the value comparison.
    """

    def __init__(self, document, *args, **kwargs):
        self.document = document
        super().__init__(*args, **kwargs)

    def set_state(self, state, model=None):
        result = super().set_state(state, model)
        if self.state != self.document.state_edoc:
            self.document.write({"state_edoc": self.state})
        return result


class Document(models.Model):
    """
    Fiscal Document EDI extension implementing State Machine workflow.
    """

    _inherit = "l10n_br_fiscal.document"

    state_edoc = fields.Selection(
        selection_add=DOCUMENT_STATES,
        ondelete={
            DOCUMENT_STATE_SENDING: "set default",
            DOCUMENT_STATE_AUTHORIZED: "set default",
            DOCUMENT_STATE_REJECTED: "set default",
            DOCUMENT_STATE_DENIED: "set default",
        },
    )

    event_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.event",
        inverse_name="document_id",
        string="Events",
        copy=False,
        readonly=True,
    )

    correction_event_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.event",
        inverse_name="document_id",
        domain=[("type", "=", "14")],
        string="Correction Events",
        copy=False,
        readonly=True,
    )

    issuer = fields.Selection(
        selection=DOCUMENT_ISSUER,
        default=DOCUMENT_ISSUER_COMPANY,
    )

    status_code = fields.Char(
        copy=False,
    )

    status_name = fields.Char(
        copy=False,
    )

    status_description = fields.Char(
        compute="_compute_status_description",
        copy=False,
    )

    # Authorization Event Related Fields
    authorization_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.event",
        string="Authorization Event",
        readonly=True,
        copy=False,
    )

    authorization_date = fields.Datetime(
        related="authorization_event_id.protocol_date",
        string="Authorization Protocol Date",
    )

    authorization_protocol = fields.Char(
        related="authorization_event_id.protocol_number",
        string="Authorization Protocol Number",
    )

    send_file_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="authorization_event_id.file_request_id",
        string="Send Document File XML",
        ondelete="restrict",
        readonly=True,
    )

    authorization_file_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="authorization_event_id.file_response_id",
        string="Authorization File XML",
        ondelete="restrict",
        readonly=True,
    )

    # Cancel Event Related Fields
    cancel_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.event",
        string="Cancel Event",
        copy=False,
    )

    cancel_date = fields.Datetime(
        related="cancel_event_id.protocol_date",
        string="Cancel Protocol Date",
    )

    cancel_protocol_number = fields.Char(
        related="cancel_event_id.protocol_number",
        string="Cancel Protocol Protocol",
    )

    cancel_file_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="cancel_event_id.file_response_id",
        string="Cancel File XML",
        ondelete="restrict",
        readonly=True,
    )

    cancel_reason = fields.Char()

    correction_reason = fields.Char()

    # Invalidate Event Related Fields
    invalidate_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.event",
        string="Invalidate Event",
        copy=False,
    )

    invalidate_date = fields.Datetime(
        related="invalidate_event_id.protocol_date",
        string="Invalidate Protocol Date",
    )

    invalidate_protocol_number = fields.Char(
        related="invalidate_event_id.protocol_number",
        string="Invalidate Protocol Number",
    )

    invalidate_file_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="invalidate_event_id.file_response_id",
        string="Invalidate File XML",
        ondelete="restrict",
        readonly=True,
    )

    document_version = fields.Char(string="Version", default="4.00", readonly=True)

    is_edoc_printed = fields.Boolean(string="Is Printed?", readonly=True)

    file_report_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Document Report",
        ondelete="restrict",
        readonly=True,
        copy=False,
    )

    @api.depends("status_code", "status_name")
    def _compute_status_description(self):
        for record in self:
            if record.status_code:
                record.status_description = "{} - {}".format(
                    record.status_code or "",
                    record.status_name or "",
                )
            else:
                record.status_description = False

    @api.constrains("issuer")
    def _check_issuer(self):
        for record in self.filtered(lambda d: d.document_electronic):
            if not record.issuer:
                raise ValidationError(
                    _(
                        "The field 'Issuer' is required for brazilian electronic "
                        "documents!"
                    )
                )

    # -------------------------------------------------------------------------
    # State Machine Logic
    # -------------------------------------------------------------------------

    def get_state_machine_config(self):
        self.ensure_one()
        return {
            "states": [
                DOCUMENT_STATE_DRAFT,
                DOCUMENT_STATE_OPEN,
                DOCUMENT_STATE_SENDING,
                DOCUMENT_STATE_AUTHORIZED,
                DOCUMENT_STATE_REJECTED,
                DOCUMENT_STATE_DENIED,
                DOCUMENT_STATE_CANCEL,
                # Terminal state (no outgoing transition), but it must be
                # known to the machine: building it with an unknown initial
                # state raises ValueError.
                DOCUMENT_STATE_INVALIDATED,
            ],
            "transitions": [
                # Validate: Draft -> Open
                {
                    "trigger": "action_validate",
                    "source": DOCUMENT_STATE_DRAFT,
                    "dest": DOCUMENT_STATE_OPEN,
                    "before": "_before_document_validate",
                },
                # Send: Open/Rejected/Sending -> Sending
                # SENDING is included as a source so that documents stuck in
                # 'enviada' (e.g. after an async receipt consult is needed)
                # can be re-sent. The NFe module uses this to consult the
                # receipt of an async batch or retransmit.
                {
                    "trigger": "action_send",
                    "source": [
                        DOCUMENT_STATE_OPEN,
                        DOCUMENT_STATE_REJECTED,
                        DOCUMENT_STATE_SENDING,
                    ],
                    "dest": DOCUMENT_STATE_SENDING,
                    "before": "_before_document_send",
                    "after": "_after_document_send",
                },
                # Authorize after send: Sending/Open/Rejected -> Authorized
                # REJECTED is a valid source for the SEFAZ sync rescue path:
                # when a document is rejected locally (e.g. duplicate key
                # cStat 539) but is actually authorized at SEFAZ, the consult
                # must transition it to authorized with callbacks so the
                # DANFE is generated (_after_document_authorize).
                {
                    "trigger": "action_authorize",
                    "source": [
                        DOCUMENT_STATE_SENDING,
                        DOCUMENT_STATE_OPEN,
                        DOCUMENT_STATE_REJECTED,
                    ],
                    "dest": DOCUMENT_STATE_AUTHORIZED,
                    "after": "_after_document_authorize",
                },
                # Direct authorize: Draft -> Authorized
                # Used by non-electronic company docs and partner-issued docs
                # (imported supplier NF-e already authorized externally).
                # Runs _before_document_validate for numbering/date/comments.
                {
                    "trigger": "action_confirm_authorized",
                    "source": DOCUMENT_STATE_DRAFT,
                    "dest": DOCUMENT_STATE_AUTHORIZED,
                    "before": "_before_document_validate",
                    "after": "_after_document_authorize",
                },
                # Reject: Sending -> Rejected
                {
                    "trigger": "action_reject",
                    "source": [DOCUMENT_STATE_SENDING, DOCUMENT_STATE_OPEN],
                    "dest": DOCUMENT_STATE_REJECTED,
                },
                # Deny: Sending/Open/Rejected -> Denied
                # REJECTED is a valid source for the SEFAZ sync rescue path
                # (same rationale as action_authorize above).
                {
                    "trigger": "action_deny",
                    "source": [
                        DOCUMENT_STATE_SENDING,
                        DOCUMENT_STATE_OPEN,
                        DOCUMENT_STATE_REJECTED,
                    ],
                    "dest": DOCUMENT_STATE_DENIED,
                    "after": "_after_document_deny",
                },
                # Cancel: Authorized/Open/Draft/Sending -> Cancel
                # SENDING (enviada) is a valid source because the NFSe
                # Focus status sync reports municipal cancellations while
                # the document is still awaiting authorization.  The
                # municipal webservice is the authoritative source for
                # NFSe cancellation.  For NFe, the cancel wizard handles
                # the SEFAZ cancel event before _document_cancel is called.
                # REJECTED is NOT a valid source: a rejection doesn't
                # consume numbering so there is nothing to cancel.
                {
                    "trigger": "action_cancel_fsm",
                    "source": [
                        DOCUMENT_STATE_AUTHORIZED,
                        DOCUMENT_STATE_OPEN,  # Allow canceling if manual/not sent
                        DOCUMENT_STATE_DRAFT,
                        DOCUMENT_STATE_SENDING,
                    ],
                    "dest": DOCUMENT_STATE_CANCEL,
                    "before": "_before_document_cancel",
                },
                # Back to Draft
                # SENDING (enviada) is NOT a valid source: a doc being
                # processed by SEFAZ could be edited and re-sent with the
                # same key while the batch is in flight.  DENIED (denegada)
                # is NOT a valid source: denial is definitive and consumes
                # the numbering.  The SPED guard in the before callback
                # provides an additional safety net.
                # DRAFT self-loop is handled by an early return in
                # action_document_back2draft for idempotency.
                {
                    "trigger": "action_draft_fsm",
                    "source": [
                        DOCUMENT_STATE_OPEN,
                        DOCUMENT_STATE_REJECTED,
                        DOCUMENT_STATE_CANCEL,
                    ],
                    "dest": DOCUMENT_STATE_DRAFT,
                    "before": "_before_document_back2draft",
                },
            ],
            "initial": self.state_edoc,
        }

    def _resolve_fsm_transition(self, transition):
        """Bind the string callbacks of a transition definition to this record.

        The machine's model is the machine itself (Odoo recordsets are
        slotted and cannot carry trigger methods), so callback names such as
        "_before_document_validate" are resolved to bound methods here,
        keeping get_state_machine_config() a declarative, string-based API
        that submodules can extend with super().
        """
        resolved = dict(transition)
        for key in ("before", "after", "conditions"):
            if key in resolved:
                callbacks = resolved[key]
                if isinstance(callbacks, str):
                    callbacks = [callbacks]
                resolved[key] = [getattr(self, cb) for cb in callbacks]
        return resolved

    def _trigger_fsm(self, trigger):
        for doc in self:
            try:
                config = doc.get_state_machine_config()
                machine = FiscalDocumentStateMachine(
                    doc,
                    states=config["states"],
                    transitions=[
                        doc._resolve_fsm_transition(t) for t in config["transitions"]
                    ],
                    initial=config["initial"],
                    ignore_invalid_triggers=False,
                )
                getattr(machine, trigger)()
            except MachineError as e:
                raise UserError(
                    _("State transition failed for action '%(action)s': %(error)s")
                    % {"action": trigger, "error": e}
                ) from e

    def _document_cancel(self, justificative=None):
        if justificative:
            self.cancel_reason = justificative
        self._trigger_fsm("action_cancel_fsm")

    def _document_correction(self, justificative):
        """Record the correction reason. Specific document modules override
        this method to transmit the correction event (CC-e)."""
        self.ensure_one()
        self.correction_reason = justificative

    # -------------------------------------------------------------------------
    # Transition Callbacks
    # -------------------------------------------------------------------------

    def _before_document_validate(self):
        self._document_date()
        self._document_number()
        self._copy_operation_comments()
        self._document_comment()
        self._document_check()
        if self.issuer == DOCUMENT_ISSUER_COMPANY:
            # Only company-issued documents export XML and create the
            # authorization event. Partner-issued documents (imported
            # supplier NF-e) are already authorized externally and may
            # not have a document_serie_id, which the event creation
            # requires.
            self._document_export()

    def _before_document_send(self):
        # Placeholder for pre-send checks
        pass

    def _after_document_send(self):
        # Trigger actual sending logic
        self._document_send_logic()

    def _after_document_authorize(self):
        """Hook called after the document is authorized. Overridden by
        transmission modules (e.g. l10n_br_nfe generates the DANFE here)."""
        pass

    def _before_document_cancel(self):
        # Logic moved from _document_cancel
        if self.issuer == DOCUMENT_ISSUER_COMPANY:
            # If authorized, we need to call SEFAZ cancellation
            # This is usually done via Wizard, so this transition might be triggered
            # AFTER the wizard logic.
            # If triggered directly, ensure we have a reason if required.
            pass
        # Return True to match the legacy _exec_before_SITUACAO_EDOC_CANCELADA
        # contract: providers that override this hook chain the super() result
        # and rely on it being truthy when they have nothing to do.
        return True

    def _before_document_back2draft(self):
        self.ensure_one()
        if self.state_fiscal in SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO:
            raise UserError(
                _(
                    "You cannot return the document to draft when its "
                    "fiscal state is %(fiscal_state)s, as it has already "
                    "been recorded as cancelled for SPED purposes.",
                    fiscal_state=self.state_fiscal,
                )
            )
        self.xml_error_message = False
        self.file_report_id = False

    # -------------------------------------------------------------------------
    # Logic Implementation (Ported from Workflow/Mixin)
    # -------------------------------------------------------------------------

    def _document_date(self):
        if not self.document_date:
            self.document_date = fields.Datetime.now()
        if not self.date_in_out:
            self.date_in_out = fields.Datetime.now()

    def _document_check(self):
        return True

    def _copy_operation_comments(self):
        """Copy the default comments of the fiscal operation to the document
        and its lines, so _document_comment() can render them."""
        for record in self:
            if not record.comment_ids and record.fiscal_operation_id.comment_ids:
                record.comment_ids |= record.fiscal_operation_id.comment_ids
            for line in record.fiscal_line_ids:
                if not line.comment_ids and line.fiscal_operation_line_id.comment_ids:
                    line.comment_ids |= line.fiscal_operation_line_id.comment_ids

    def _generate_key(self):
        for record in self:
            if record.document_type_id.code in (
                MODELO_FISCAL_NFE,
                MODELO_FISCAL_NFCE,
                MODELO_FISCAL_CTE,
                MODELO_FISCAL_MDFE,
            ):
                date = fields.Datetime.context_timestamp(record, record.document_date)
                chave_edoc = ChaveEdoc(
                    ano_mes=date.strftime("%y%m").zfill(4),
                    cnpj_cpf_emitente=record.company_id.vat,
                    codigo_uf=(
                        record.company_id.state_id
                        and record.company_id.state_id.ibge_code
                        or ""
                    ),
                    forma_emissao=1,  # TODO: Implementar campo no Odoo
                    modelo_documento=record.document_type_id.code or "",
                    numero_documento=record.document_number or "",
                    numero_serie=record.document_serie or "",
                    validar=False,
                )
                record.key_random_code = chave_edoc.codigo_aleatorio
                record.key_check_digit = chave_edoc.digito_verificador
                record.document_key = chave_edoc.chave

    def _document_number(self):
        self.ensure_one()
        if self.issuer == DOCUMENT_ISSUER_COMPANY:
            if self.document_serie_id:
                self.document_serie = self.document_serie_id.code

                if self.document_type == MODELO_FISCAL_NFSE and not self.rps_number:
                    self.rps_number = self.document_serie_id.next_seq_number()

                if (
                    self.document_type != MODELO_FISCAL_NFSE
                    and not self.document_number
                ):
                    self.document_number = self.document_serie_id.next_seq_number()

            if not self.operation_name:
                self.operation_name = ", ".join(
                    [
                        line.name
                        for line in self.fiscal_line_ids.mapped("fiscal_operation_id")
                    ]
                )

            if self.document_electronic and not self.document_key:
                self._generate_key()

    def _document_send_logic(self):
        """
        Logic to handle document sending.
        Separates electronic vs non-electronic handling.
        """
        no_electronic = self.filtered(
            lambda d: (
                not d.document_electronic or not d.issuer == DOCUMENT_ISSUER_COMPANY
            )
        )
        # Non-electronic/partner-issued docs go straight to Authorized:
        # there is nothing to transmit.
        for doc in no_electronic:
            doc._trigger_fsm("action_authorize")

        electronic = self - no_electronic
        electronic._eletronic_document_send()

    def _eletronic_document_send(self):
        """
        Implement this method in your transmission module.
        """
        for record in self.filtered(filter_processador):
            # Simulate immediate authorization for 'No Processor'
            record._trigger_fsm("action_authorize")

    def _document_export(self, **kwargs):
        pass

    def _document_status(self):
        """Return the document status as text and, when needed, update the
        document status. Hook meant to be overridden by transmission modules
        (l10n_br_nfe, l10n_br_nfse_focus...)."""
        return None

    def _edoc_processor(self):
        """Hook meant to return the erpbrasil.edoc processor of the document.
        Overridden by transmission modules."""
        return None

    def _document_qrcode(self):
        """Hook meant to compute the document QR Code (NFC-e, CT-e...).
        Overridden by transmission modules."""
        pass

    def _validate_xml(self, xml_file):
        """Hook meant to validate the document XML against its schema.
        Overridden by transmission modules."""
        pass

    def _direct_draft_send(self):
        """When it returns True, the document is sent right after being
        confirmed (draft -> open -> sending in a single action). Meant to be
        overridden by modules such as POS/NFC-e ones."""
        return False

    def serialize(self):
        """
        Serialize the document to a list of EDocs (objects from erpbrasil.edoc).
        Modules should override _serialize to add their EDocs.
        """
        edocs = []
        self._serialize(edocs)
        return edocs

    def _serialize(self, edocs):
        """
        Hook for modules to add their serialized EDocs to the list.
        """
        return edocs

    def _get_state_to_action_map(self):
        return {
            DOCUMENT_STATE_OPEN: "action_validate",
            DOCUMENT_STATE_SENDING: "action_send",
            DOCUMENT_STATE_AUTHORIZED: "action_authorize",
            DOCUMENT_STATE_REJECTED: "action_reject",
            DOCUMENT_STATE_DENIED: "action_deny",
            DOCUMENT_STATE_CANCEL: "action_cancel_fsm",
            DOCUMENT_STATE_DRAFT: "action_draft_fsm",
        }

    def _change_state(self, state, force_change=False):
        """
        Wrapper to trigger state changes via FSM for legacy compatibility.
        """
        # Map legacy states to triggers if possible, or just update state_edoc
        # The FSM manages state_edoc, but 'transitions' allows direct assignment
        # if not locked. However, to respect the FSM flow, we should try triggers.
        # But 'state' argument here is the target state (e.g. 'authorized'),
        # not an action.

        # Mapping target state to action
        state_to_action = self._get_state_to_action_map()

        trigger = state_to_action.get(state)
        for record in self:
            if trigger:
                # If we are already in the target state, do nothing unless
                # forced?
                if record.state_edoc == state and not force_change:
                    continue

                # Try to trigger the transition
                try:
                    record._trigger_fsm(trigger)
                except UserError as e:
                    # If transition fails (e.g. invalid source state), we might
                    # force it if the legacy code demands it (e.g. SEFAZ sync).
                    # In legacy code, _change_state often just wrote the field.
                    if force_change:
                        record.write({"state_edoc": state})
                    else:
                        raise e
            else:
                # If no transition defined, fallback to write
                record.write({"state_edoc": state})

    # -------------------------------------------------------------------------
    # Actions / Buttons
    # -------------------------------------------------------------------------

    def action_document_confirm(self):
        """Override base button to trigger FSM validation.

        This method must be idempotent because account.move._post() may call it
        again for already confirmed documents.

        - Electronic company-issued docs: draft -> open (action_validate),
          then optionally send if _direct_draft_send().
        - Non-electronic company docs: draft -> authorized (action_authorize),
          skipping the sending step since there is nothing to transmit.
        - Partner-issued docs (imported supplier NF-e): draft -> authorized
          (action_authorize), since they are already authorized externally.

        All paths go through _before_document_validate (numbering, date,
        operation comments) to avoid the regression where non-electronic
        and partner docs were confirmed without numbering.
        """
        for doc in self:
            if doc.state_edoc != DOCUMENT_STATE_DRAFT:
                continue  # idempotent: already confirmed
            if doc.document_electronic and doc.issuer == DOCUMENT_ISSUER_COMPANY:
                doc._trigger_fsm("action_validate")
                if doc._direct_draft_send():
                    doc.action_document_send()
            else:
                # Non-electronic or partner-issued: confirm straight to
                # authorized. The action_confirm_authorized transition runs
                # _before_document_validate for numbering/date, then
                # _after_document_authorize for any post-auth hook.
                doc._trigger_fsm("action_confirm_authorized")
        return True

    def action_document_send(self):
        """Trigger Sending"""
        return self._trigger_fsm("action_send")

    def action_document_back2draft(self):
        """Override base button"""
        if self.document_electronic and self.issuer == DOCUMENT_ISSUER_COMPANY:
            if self.state_edoc == DOCUMENT_STATE_DRAFT:
                return True  # idempotent: already in draft
            return self._trigger_fsm("action_draft_fsm")
        else:
            return super().action_document_back2draft()

    def action_document_cancel(self):
        """Override base button"""
        if self.state_edoc in (
            DOCUMENT_STATE_CANCEL,
            DOCUMENT_STATE_DENIED,
            DOCUMENT_STATE_INVALIDATED,
        ):
            return True

        if self.document_electronic and self.issuer == DOCUMENT_ISSUER_COMPANY:
            # For authorized docs, show wizard
            if self.state_edoc == DOCUMENT_STATE_AUTHORIZED:
                return self.env["ir.actions.act_window"]._for_xml_id(
                    "l10n_br_fiscal_edi.document_cancel_wizard_action"
                )
            # Otherwise trigger FSM cancel
            return self._trigger_fsm("action_cancel_fsm")
        else:
            return super().action_document_cancel()

    def action_document_correction(self):
        """Open the correction wizard for authorized company-issued documents."""
        self.ensure_one()
        if (
            self.state_edoc == DOCUMENT_STATE_AUTHORIZED
            and self.issuer == DOCUMENT_ISSUER_COMPANY
        ):
            return self.env["ir.actions.act_window"]._for_xml_id(
                "l10n_br_fiscal_edi.document_correction_wizard_action"
            )
        raise UserError(
            _(
                "You can only create a fiscal correction for authorized "
                "documents issued by your company."
            )
        )

    def action_document_invalidate(self):
        """Open the number invalidation wizard for company-issued documents
        that are in a state where the number was consumed but the document
        can still be invalidated (rejected/denied).
        """
        self.ensure_one()
        if self.issuer == DOCUMENT_ISSUER_COMPANY and self.state_edoc in (
            DOCUMENT_STATE_REJECTED,
            DOCUMENT_STATE_DENIED,
        ):
            return self.env["ir.actions.act_window"]._for_xml_id(
                "l10n_br_fiscal_edi.invalidate_number_wizard_action"
            )
        raise UserError(
            _(
                "You can only invalidate the numbering of rejected or denied "
                "documents issued by your company."
            )
        )

    def _after_document_deny(self):
        """Hook called after document denial. Override in account module."""
        pass

    # -------------------------------------------------------------------------
    # Misc Tools
    # -------------------------------------------------------------------------

    def _target_new_tab(self, attachment_id):
        if attachment_id:
            return {
                "type": "ir.actions.act_url",
                "url": f"/web/content/{attachment_id.id}/{attachment_id.name}",
                "target": "new",
            }

    def view_xml(self):
        self.ensure_one()
        xml_file = self.authorization_file_id or self.send_file_id
        if not xml_file:
            self._document_export()
            xml_file = self.authorization_file_id or self.send_file_id
        if not xml_file:
            raise UserError(_("No XML file generated!"))
        return self._target_new_tab(xml_file)

    def make_pdf(self):
        pass

    def _download_url(self, attachment):
        return f"/web/content/{attachment.id}/{attachment.name}?download=true"

    def _xml_attachment(self):
        """The authorized XML, and the sent one while authorization has not come."""
        self.ensure_one()
        return self.authorization_file_id or self.send_file_id

    def _report_attachment(self):
        self.ensure_one()
        if not self.file_report_id:
            self.make_pdf()
        return self.file_report_id

    def _collect_download_files(self, xml=True, report=True):
        """Files to hand to the browser, and the documents left without any.

        A document still in typing has nothing to give, and a selection of many
        notes usually mixes those with the authorized ones. Refusing the whole
        batch because of one of them is worse than handing over what exists and
        naming what was left out, so the ones without a file come back apart
        instead of raising.
        """
        files = []
        skipped = self.browse()
        for record in self:
            attachments = self.env["ir.attachment"]
            if xml:
                attachments |= record._xml_attachment()
            if report:
                attachments |= record._report_attachment()
            if not attachments:
                skipped |= record
                continue
            files.extend(
                {"url": record._download_url(each), "name": each.name}
                for each in attachments
            )
        return files, skipped

    def action_download_files(self, xml=True, report=True):
        """Hand the files over one by one, unzipped.

        A download of the browser carries one file, so who walks the list is the
        client: the action below receives the addresses and asks for one at a
        time. From three files on the browser asks the person once whether to
        accept several, which is the price of not zipping.
        """
        files, skipped = self._collect_download_files(xml=xml, report=report)
        if not files:
            raise UserError(
                _(
                    "None of the selected documents has a file to download. A "
                    "document still in typing has no XML and no report yet."
                )
            )
        return {
            "type": "ir.actions.client",
            "tag": "l10n_br_fiscal_edi.download_files",
            "params": {
                "files": files,
                "skipped": skipped.mapped("display_name"),
            },
        }

    def action_download_xml(self):
        return self.action_download_files(report=False)

    def action_download_report(self):
        return self.action_download_files(xml=False)

    def action_download_xml_and_report(self):
        return self.action_download_files()

    def view_pdf(self):
        self.ensure_one()
        if not self.file_report_id or not self.authorization_file_id:
            self.make_pdf()
        if not self.file_report_id:
            raise UserError(_("No PDF file generated!"))
        return self._target_new_tab(self.file_report_id)

    # -------------------------------------------------------------------------
    # Legacy workflow API migration table
    #
    # The old document_workflow.py mixin dispatched to these methods.
    # They were removed in the EDI FSM refactor.  If your module overrides
    # any of them, migrate to the FSM callback listed below.
    # See the ROADMAP in l10n_br_fiscal_edi and OCA PR #4629 for details.
    #
    # _exec_before_SITUACAO_EDOC_EM_DIGITACAO  -> _before_document_validate
    # _exec_before_SITUACAO_EDOC_A_ENVIAR      -> _before_document_validate
    # _exec_before_SITUACAO_EDOC_ENVIADA       -> _before_document_send
    # _exec_before_SITUACAO_EDOC_REJEITADA     -> action_reject transition
    # _exec_before_SITUACAO_EDOC_AUTORIZADA    -> _after_document_authorize
    # _exec_before_SITUACAO_EDOC_CANCELADA     -> _before_document_cancel
    # _exec_before_SITUACAO_EDOC_DENEGADA      -> action_deny transition
    # _exec_before_SITUACAO_EDOC_INUTILIZADA   -> action_document_invalidate
    # _exec_after_SITUACAO_EDOC_EM_DIGITACAO   -> _before_document_back2draft
    # _exec_after_SITUACAO_EDOC_A_ENVIAR       -> _direct_draft_send
    # _exec_after_SITUACAO_EDOC_ENVIADA        -> _after_document_send
    # _exec_after_SITUACAO_EDOC_REJEITADA      -> action_reject transition
    # _exec_after_SITUACAO_EDOC_AUTORIZADA     -> _after_document_authorize
    # _exec_after_SITUACAO_EDOC_CANCELADA      -> action_cancel_fsm transition
    # _exec_after_SITUACAO_EDOC_DENEGADA       -> _after_document_deny
    # _exec_after_SITUACAO_EDOC_INUTILIZADA    -> action_document_invalidate
    # exec_after_SITUACAO_EDOC_DENEGADA        -> _after_document_deny
    # -------------------------------------------------------------------------
