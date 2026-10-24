# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants import (
    CLOSING_IN_PROGRESS,
    DCTFWEB_CATEGORY,
    DCTFWEB_CATEGORY_GENERAL,
    SERVICES,
)


class ServiceRefused(Exception):
    """The authority answered, and the answer was no.

    Internal to this module: it never reaches the user as an exception, it is
    caught and turned into a notification so the audit log survives.
    """

    def __init__(self, messages):
        super().__init__(messages)
        self.messages = messages

    def notification(self):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "danger",
                "sticky": True,
                "title": _("The authority refused the request"),
                "message": self.messages,
            },
        }


class DctfwebAssessment(models.Model):
    """Transmission of the MIT and of the DCTFWeb it feeds.

    The business verbs live here and the transport lives in the client, so a
    change of provider does not touch the state machine.
    """

    _inherit = "l10n_br_dctfweb.assessment"

    dctfweb_category = fields.Selection(
        selection=DCTFWEB_CATEGORY,
        default=DCTFWEB_CATEGORY_GENERAL,
        required=True,
        help="Category of the DCTFWeb the MIT feeds. The monthly assessment "
        "of a legal entity is the general monthly one.",
    )
    immediate_transmission = fields.Boolean(
        default=True,
        help="Ask the authority to transmit the DCTFWeb as soon as the MIT "
        "assessment is closed, which spares signing the declaration XML.",
    )
    serpro_protocol = fields.Char(
        string="Closing protocol",
        readonly=True,
        copy=False,
        help="protocoloEncerramento: what the closing status is asked about.",
    )
    serpro_assessment_id = fields.Char(
        string="Authority assessment id",
        readonly=True,
        copy=False,
        help="idApuracao, the identifier the authority gave the assessment.",
    )
    closing_status = fields.Char(readonly=True, copy=False)
    rfb_situation = fields.Selection(
        selection=[
            ("in_progress", "In progress"),
            ("active", "Active"),
        ],
        string="Situation at the authority",
        readonly=True,
        copy=False,
        help="A declaration that was not transmitted is in progress; once it "
        "is, it becomes active.",
    )
    receipt_number = fields.Char(readonly=True, copy=False)
    declaration_xml = fields.Binary(readonly=True, copy=False, attachment=True)
    declaration_xml_filename = fields.Char(readonly=True, copy=False)
    signed_declaration_xml = fields.Binary(
        string="Signed declaration XML",
        copy=False,
        attachment=True,
        help="The declaration XML signed with the e-CNPJ certificate. The "
        "authority requires it character by character identical to the one it "
        "answered.",
    )
    darf_file = fields.Binary(readonly=True, copy=False, attachment=True)
    darf_filename = fields.Char(readonly=True, copy=False)
    full_declaration_file = fields.Binary(readonly=True, copy=False, attachment=True)
    full_declaration_filename = fields.Char(readonly=True, copy=False)
    transmission_ids = fields.One2many(
        comodel_name="l10n_br_dctfweb.transmission",
        inverse_name="assessment_id",
        string="Transmissions",
        readonly=True,
    )
    transmission_count = fields.Integer(
        compute="_compute_transmission_count",
    )

    @api.depends("transmission_ids")
    def _compute_transmission_count(self):
        for record in self:
            record.transmission_count = len(record.transmission_ids)

    # ------------------------------------------------------------------
    # Dispatch and cost warning
    # ------------------------------------------------------------------

    def _taxpayer_cnpj(self):
        self.ensure_one()
        digits = "".join(filter(str.isdigit, self.company_id.cnpj_cpf or ""))
        if len(digits) != 14:
            raise UserError(
                _("The company %s has no valid CNPJ.") % self.company_id.display_name
            )
        return digits

    def _document_filename(self, kind, extension):
        """Name a document the way the MIT file is named."""
        self.ensure_one()
        root = self._company_cnpj_root()
        return f"{root}-{kind}-{self.year}{self.month.zfill(2)}.{extension}"

    def _period_data(self):
        """The pair of fields every DCTFWeb service takes."""
        self.ensure_one()
        return {
            "categoria": self.dctfweb_category,
            "anoPA": str(self.year),
            "mesPA": self.month.zfill(2),
        }

    def _dispatch(self, service_key):
        """Run the service, or ask for confirmation when it is billed."""
        self.ensure_one()
        service = SERVICES[service_key]
        if service["billed"] and self.company_id.sudo().serpro_warn_cost:
            return {
                "type": "ir.actions.act_window",
                "res_model": "l10n_br_dctfweb.cost.warning",
                "view_mode": "form",
                "target": "new",
                "context": {
                    "default_assessment_id": self.id,
                    "default_service_key": service_key,
                },
            }
        return self.run_service(service_key)

    def run_service(self, service_key):
        """Call one service and let its handler read the answer.

        A refusal from the authority is caught here and reported as a
        notification, on purpose. Raising it would roll the transaction back
        and delete the very log entry that explains the refusal, so the
        refusal has to travel as a return value.
        """
        self.ensure_one()
        handler = getattr(self, "_serpro_%s" % service_key)
        try:
            return handler()
        except ServiceRefused as refusal:
            return refusal.notification()

    def _call(self, service_key, data):
        """Call the transport and keep the trail."""
        self.ensure_one()
        transport = self.env["l10n_br_dctfweb.integra.contador"]
        request = transport._build_request(
            self.company_id, self._taxpayer_cnpj(), service_key, data
        )
        body = transport.call(
            self.company_id, self._taxpayer_cnpj(), service_key, data, record=self
        )
        transmission = self.env["l10n_br_dctfweb.transmission"].log(
            self, service_key, request, body
        )
        messages = transmission.messages or _("no message")
        self.message_post(
            body=_("%(service)s: %(messages)s")
            % {"service": SERVICES[service_key]["name"], "messages": messages}
        )
        if not transmission.success:
            raise ServiceRefused(messages)
        return body, transmission

    @api.model
    def _answer_data(self, body):
        data = body.get("dados")
        return data if isinstance(data, dict) else {}

    # ------------------------------------------------------------------
    # MIT
    # ------------------------------------------------------------------

    def action_serpro_close_mit(self):
        return self._dispatch("close_assessment")

    def _serpro_close_assessment(self):
        """Close the MIT assessment at the authority.

        The service takes the very payload the import file carries, plus the
        flag that asks for the DCTFWeb to be transmitted right away.
        """
        self.ensure_one()
        if self.state not in ("assessed", "closed"):
            raise UserError(_("Close the MIT locally before sending it."))
        pendencies = self._check_pendencies()
        if pendencies:
            raise UserError(
                _("The MIT still has pendencies:\n%s")
                % "\n".join("- %s" % pendency for pendency in pendencies)
            )
        data = self._build_mit_payload()
        data["TransmissaoImediata"] = self.immediate_transmission
        body, dummy = self._call("close_assessment", data)
        answer = self._answer_data(body)
        values = {
            "serpro_protocol": answer.get("protocoloEncerramento") or False,
            "state": "closed",
        }
        if answer.get("idApuracao") is not None:
            values["serpro_assessment_id"] = str(answer.get("idApuracao"))
        if self.immediate_transmission:
            values.update({"state": "transmitted", "rfb_situation": "active"})
        else:
            values["rfb_situation"] = "in_progress"
        self.write(values)
        return True

    def action_serpro_closing_status(self):
        return self._dispatch("closing_status")

    def _serpro_closing_status(self):
        """Ask whether the asynchronous closing has finished."""
        self.ensure_one()
        if not self.serpro_protocol:
            raise UserError(_("Close the MIT at the authority first."))
        body, dummy = self._call(
            "closing_status", {"protocoloEncerramento": self.serpro_protocol}
        )
        answer = self._answer_data(body)
        status = answer.get("situacaoEncerramento") or answer.get("situacao")
        self.closing_status = status or False
        if status and status != CLOSING_IN_PROGRESS:
            identifier = answer.get("idApuracao")
            if identifier is not None:
                self.serpro_assessment_id = str(identifier)
        return True

    def action_serpro_consult_assessment(self):
        return self._dispatch("consult_assessment")

    def _serpro_consult_assessment(self):
        self.ensure_one()
        if not self.serpro_assessment_id:
            raise UserError(_("The authority has not given this MIT an id yet."))
        self._call("consult_assessment", {"idApuracao": int(self.serpro_assessment_id)})
        return True

    def action_serpro_list_assessments(self):
        return self._dispatch("list_assessments")

    def _serpro_list_assessments(self):
        self.ensure_one()
        self._call(
            "list_assessments",
            {"anoApuracao": str(self.year), "mesApuracao": self.month.zfill(2)},
        )
        return True

    # ------------------------------------------------------------------
    # DCTFWeb
    # ------------------------------------------------------------------

    def action_serpro_fetch_xml(self):
        return self._dispatch("declaration_xml")

    def _serpro_declaration_xml(self):
        """Fetch the declaration XML, which is what gets signed and sent."""
        self.ensure_one()
        body, dummy = self._call("declaration_xml", self._period_data())
        content = body.get("dados")
        if isinstance(content, dict):
            content = content.get("xml") or content.get("xmlDeclaracao")
        if not content:
            raise ServiceRefused(_("The authority answered no declaration XML."))
        self.write(
            {
                "declaration_xml": content
                if isinstance(content, str)
                else base64.b64encode(content),
                "declaration_xml_filename": self._document_filename("DCTFWeb", "xml"),
            }
        )
        return True

    def action_serpro_transmit_dctfweb(self):
        return self._dispatch("transmit_declaration")

    def _serpro_transmit_declaration(self):
        """Transmit the signed declaration XML.

        Only needed when the MIT was closed without immediate transmission:
        the authority requires the XML it answered, signed and otherwise
        untouched, character by character.
        """
        self.ensure_one()
        if not self.signed_declaration_xml:
            raise UserError(
                _(
                    "Fetch the declaration XML, sign it with the e-CNPJ "
                    "certificate and attach it before transmitting. Closing "
                    "the MIT with immediate transmission avoids this step."
                )
            )
        data = self._period_data()
        data["xmlAssinadoBase64"] = (
            self.signed_declaration_xml.decode()
            if isinstance(self.signed_declaration_xml, bytes)
            else self.signed_declaration_xml
        )
        body, dummy = self._call("transmit_declaration", data)
        receipt = body.get("dados")
        if isinstance(receipt, dict):
            receipt = receipt.get("numeroRecibo")
        self.write(
            {
                "state": "transmitted",
                "rfb_situation": "active",
                "receipt_number": str(receipt) if receipt else False,
            }
        )
        return True

    def action_serpro_receipt(self):
        return self._dispatch("declaration_receipt")

    def _serpro_declaration_receipt(self):
        self.ensure_one()
        body, dummy = self._call("declaration_receipt", self._period_data())
        answer = body.get("dados")
        if isinstance(answer, dict):
            self.receipt_number = (
                answer.get("numeroRecibo") or self.receipt_number or False
            )
        return True

    def action_serpro_full_declaration(self):
        return self._dispatch("full_declaration")

    def _serpro_full_declaration(self):
        self.ensure_one()
        body, dummy = self._call("full_declaration", self._period_data())
        content = self._pdf_from_answer(body)
        if content:
            self.write(
                {
                    "full_declaration_file": content,
                    "full_declaration_filename": self._document_filename(
                        "DCTFWeb", "pdf"
                    ),
                }
            )
        return True

    def action_serpro_issue_darf(self):
        service = (
            "issue_darf" if self.state == "transmitted" else "issue_darf_in_progress"
        )
        return self._dispatch(service)

    def _serpro_issue_darf(self):
        return self._issue_darf("issue_darf")

    def _serpro_issue_darf_in_progress(self):
        return self._issue_darf("issue_darf_in_progress")

    def _issue_darf(self, service_key):
        """Issue the numbered DARF, before or after the declaration closes."""
        self.ensure_one()
        body, dummy = self._call(service_key, self._period_data())
        content = self._pdf_from_answer(body)
        if not content:
            raise ServiceRefused(_("The authority answered no collection document."))
        self.write(
            {
                "darf_file": content,
                "darf_filename": self._document_filename("DARF", "pdf"),
            }
        )
        return True

    @api.model
    def _pdf_from_answer(self, body):
        """The authority answers a document as base64 under a few names."""
        answer = body.get("dados")
        if isinstance(answer, str):
            return answer
        if not isinstance(answer, dict):
            return False
        for key in ("pdf", "documento", "arquivo", "docArrecadacao"):
            if answer.get(key):
                return answer[key]
        return False

    def action_view_transmissions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Transmissions"),
            "res_model": "l10n_br_dctfweb.transmission",
            "view_mode": "tree,form",
            "domain": [("assessment_id", "=", self.id)],
        }
