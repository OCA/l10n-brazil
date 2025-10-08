# Copyright (C) 2019  Renato Lima - Akretion
# Copyright (C) 2019  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from transitions import Machine, MachineError

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER,
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_STATE_CANCEL,
    DOCUMENT_STATE_DRAFT,
    DOCUMENT_STATE_OPEN,
    PROCESSADOR_NENHUM,
)
from odoo.addons.l10n_br_fiscal_edi.constants.fiscal import (
    DOCUMENT_STATE_AUTHORIZED,
    DOCUMENT_STATE_REJECTED,
    DOCUMENT_STATE_SEND,
    DOCUMENT_STATES,
)


def filter_processador(record):
    if record.document_electronic and record.processador_edoc == PROCESSADOR_NENHUM:
        return True
    return False


class Document(models.Model):
    """
    As of August 2024, this is the extraction of the legacy
    l10n_br_fiscal.document.electronic mixin that was part of l10n_br_fiscal
    from version 12 to 14. This code was made before the OCA/edi and OCA/edi-framework
    and might easily be improved...
    """

    _name = "l10n_br_fiscal.document"

    _inherit = [
        "l10n_br_fiscal.document",
        "l10n_br_fiscal.document.workflow",
    ]

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

    state = fields.Selection(
        add_selection=DOCUMENT_STATES,
    )

    def get_state_machine_config(self):
        self.ensure_one()
        state_machine_config = {
            "states": [
                DOCUMENT_STATE_DRAFT,
                DOCUMENT_STATE_OPEN,
                DOCUMENT_STATE_CANCEL,
                DOCUMENT_STATE_SEND,
                DOCUMENT_STATE_AUTHORIZED,
                DOCUMENT_STATE_REJECTED,
            ],
            "transitions": [
                {
                    "trigger": "action_validate",
                    "source": DOCUMENT_STATE_DRAFT,
                    "dest": DOCUMENT_STATE_SEND,
                    "before": self._before_document_validate,
                    "after": self._after_document_validate,
                },
                {
                    "trigger": "action_send",
                    "source": DOCUMENT_STATE_SEND,
                    "dest": DOCUMENT_STATE_OPEN,
                    "before": self._before_document_send,
                    "after": self._after_document_send
                },
                {
                    "trigger": "action_cancel",
                    "source": [DOCUMENT_STATE_SEND, DOCUMENT_STATE_CANCEL],
                    "dest": DOCUMENT_STATE_CANCEL,
                    "before": self._before_document_cancel,
                    "after": self._after_document_cancel,
                },
                {
                    "trigger": "action_draft",
                    "source": [
                        DOCUMENT_STATE_OPEN,
                        DOCUMENT_STATE_SEND,
                        DOCUMENT_STATE_CANCEL,
                    ],
                    "dest": DOCUMENT_STATE_DRAFT,
                    "before": self._before_document_draft,
                    "after": self._after_document_draft,
                },
            ],
            "after_state_change": self._after_trigger_fsm,
            "initial": self.state,
        }
        return state_machine_config

    def _trigger_fsm(self, trigger):
        """
        Helper method to trigger a state transition, reducing code repetition.
        :param trigger: The name of the trigger/event to fire.
        """
        for doc in self:
            try:
                state_machine_config = self.get_state_machine_config()
                machine = Machine(
                    states=state_machine_config["states"],
                    transitions=state_machine_config["transitions"],
                    initial=state_machine_config["initial"],
                    after_state_change=state_machine_config["after_state_change"],
                )
                # Dynamically call the trigger method on the machine instance
                getattr(machine, trigger)()
            except MachineError as e:
                raise UserError(
                    _("State transition failed for action '%(action)s': %(error)s")
                    % {"action": trigger, "error": e}
                )

    def _after_state_change(self):
        # TODO Update Odoo document state field
        pass

    # these workflow methods are plugged here so their interface defined in
    # l10n_br_fiscal can easily be overriden in other modules.
    def button_open(self):
        """Transição para o estado 'Validado'."""
        self._trigger_fsm("action_validate")

    def button_cancel(self):
        """Transição para o estado 'Cancelado'."""
        self._trigger_fsm("action_cancel")

    def button_draft(self):
        """Transição para o estado 'Cancelado'."""
        self._trigger_fsm("action_cancel")

    def button_send(self):
        """Transição para o estado 'Enviado'."""
        self._trigger_fsm("action_send")

    def action_document_invalidate(self):
        super().action_document_invalidate()
        return self._action_document_invalidate()

    def action_document_correction(self):
        super().action_document_correction()
        return self._action_document_correction()

    def exec_after_SITUACAO_EDOC_DENEGADA(self, old_state, new_state):
        # see https://github.com/OCA/l10n-brazil/pull/3272
        super().exec_after_SITUACAO_EDOC_DENEGADA(old_state, new_state)
        return self._exec_after_SITUACAO_EDOC_DENEGADA(old_state, new_state)

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

    def _eletronic_document_send(self):
        """Implement this method in your transmission module,
        to send the electronic document and use the method _change_state
        to update the state of the transmited document,

        def _eletronic_document_send(self):
            super()._document_send()
            for record in self.filtered(myfilter):
                Do your transmission stuff
                [...]
                Change the state of the document
        """
        for record in self.filtered(filter_processador):
            record._change_state(SITUACAO_EDOC_AUTORIZADA)

    def _document_send(self):
        no_electronic = self.filtered(
            lambda d: not d.document_electronic
            or not d.issuer == DOCUMENT_ISSUER_COMPANY
        )
        no_electronic._no_eletronic_document_send()
        electronic = self - no_electronic
        electronic._eletronic_document_send()

    def serialize(self):
        edocs = []
        self._serialize(edocs)
        return edocs

    def _serialize(self, edocs):
        return edocs

    def _target_new_tab(self, attachment_id):
        if attachment_id:
            return {
                "type": "ir.actions.act_url",
                "url": f"/web/content/{attachment_id.id}/{attachment_id.name}",
                "target": "new",
            }

    def button_view_xml(self):
        self.ensure_one()
        super().view_xml()
        xml_file = self.authorization_file_id or self.send_file_id
        if not xml_file:
            self._document_export()
            xml_file = self.authorization_file_id or self.send_file_id
        if not xml_file:
            raise UserError(_("No XML file generated!"))
        return self._target_new_tab(xml_file)

    def make_pdf(self):
        pass

    def button_view_pdf(self):
        self.ensure_one()
        super().view_pdf()
        if not self.file_report_id or not self.authorization_file_id:
            self.make_pdf()
        if not self.file_report_id:
            raise UserError(_("No PDF file generated!"))
        return self._target_new_tab(self.file_report_id)

    def _document_status(self):
        """Retorna o status do documento em texto e se necessário,
        atualiza o status do documento"""
        return

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
