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


class FiscalDocumentWrapper:
    def __init__(self, document):
        self._document = document

    def __getattr__(self, name):
        return getattr(self._document, name)

    @property
    def state_edoc(self):
        return self._document.state_edoc

    @state_edoc.setter
    def state_edoc(self, value):
        self._document.write({"state_edoc": value})


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
                # Authorize after send: Sending/Open -> Authorized
                {
                    "trigger": "action_authorize",
                    "source": [
                        DOCUMENT_STATE_SENDING,
                        DOCUMENT_STATE_OPEN,
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
                # Deny: Sending -> Denied
                {
                    "trigger": "action_deny",
                    "source": [DOCUMENT_STATE_SENDING, DOCUMENT_STATE_OPEN],
                    "dest": DOCUMENT_STATE_DENIED,
                    "after": "_after_document_deny",
                },
                # Cancel: Authorized -> Cancel
                {
                    "trigger": "action_cancel_fsm",
                    "source": [
                        DOCUMENT_STATE_AUTHORIZED,
                        DOCUMENT_STATE_OPEN,  # Allow canceling if manual/not sent
                        DOCUMENT_STATE_REJECTED,
                        DOCUMENT_STATE_DRAFT,
                        DOCUMENT_STATE_SENDING,
                    ],
                    "dest": DOCUMENT_STATE_CANCEL,
                    "before": "_before_document_cancel",
                },
                # Back to Draft
                {
                    "trigger": "action_draft_fsm",
                    "source": [
                        DOCUMENT_STATE_OPEN,
                        DOCUMENT_STATE_SENDING,
                        DOCUMENT_STATE_REJECTED,
                        DOCUMENT_STATE_CANCEL,
                        DOCUMENT_STATE_DENIED,
                        DOCUMENT_STATE_DRAFT,
                    ],
                    "dest": DOCUMENT_STATE_DRAFT,
                    "before": "_before_document_back2draft",
                },
            ],
            "initial": self.state_edoc,
        }

    def _trigger_fsm(self, trigger):
        for doc in self:
            try:
                wrapper = FiscalDocumentWrapper(doc)
                config = doc.get_state_machine_config()
                Machine(
                    model=wrapper,
                    states=config["states"],
                    transitions=config["transitions"],
                    initial=config["initial"],
                    model_attribute="state_edoc",  # Bind to state_edoc
                    ignore_invalid_triggers=False,
                )
                getattr(wrapper, trigger)()
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
        self._document_export()  # Legacy hook, might be empty

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
        if trigger:
            # If we are already in the target state, do nothing unless forced?
            if self.state_edoc == state and not force_change:
                return

            # Try to trigger the transition
            try:
                self._trigger_fsm(trigger)
            except UserError as e:
                # If transition fails (e.g. invalid source state), we might force it
                # if the legacy code demands it (e.g. synchronization with SEFAZ).
                # In legacy code, _change_state often just wrote to the field.
                if force_change:
                    self.write({"state_edoc": state})
                else:
                    raise e
        else:
            # If no transition defined, fallback to write (e.g. custom states?)
            self.write({"state_edoc": state})

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

    def view_pdf(self):
        self.ensure_one()
        if not self.file_report_id or not self.authorization_file_id:
            self.make_pdf()
        if not self.file_report_id:
            raise UserError(_("No PDF file generated!"))
        return self._target_new_tab(self.file_report_id)
