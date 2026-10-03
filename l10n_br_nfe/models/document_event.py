# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import api, fields, models

from .document import NFE_XML_NAMESPACE

CORRECTION_LETTER = "14"
CORRECTION_LETTER_EVENT_CODE = "110110"


class Event(models.Model):
    _inherit = "l10n_br_fiscal.event"

    def _get_proc_evento_nfe(self):
        """Return the stored procEventoNFe of a registered correction letter.

        It is the signed event plus the answer of the tax authority, the file
        that feeds the DACCE. Events stored before it was kept (the answer
        was the SOAP envelope) have none: returns False.
        """
        self.ensure_one()
        if (
            self.type != CORRECTION_LETTER
            or self.document_id.document_type_id.code != "55"
            or not self.file_response_id
        ):
            return False
        raw = self.file_response_id.raw
        try:
            root = etree.fromstring(raw)
        except etree.XMLSyntaxError:
            return False
        if root.tag != f"{{{NFE_XML_NAMESPACE['nfe']}}}procEventoNFe":
            return False
        if (
            root.findtext(
                "nfe:evento/nfe:infEvento/nfe:tpEvento", namespaces=NFE_XML_NAMESPACE
            )
            != CORRECTION_LETTER_EVENT_CODE
            or root.find("nfe:retEvento", namespaces=NFE_XML_NAMESPACE) is None
        ):
            return False
        return raw

    def _get_dacce_issuer(self):
        """Issuer data of the DACCE header (the keys that the library reads).

        The CNPJ/CPF of the issuer comes from the XML, not from this dict.
        """
        self.ensure_one()
        partner = self.company_id.partner_id
        street = ", ".join(
            part for part in (partner.street_name, partner.street_number) if part
        )
        if partner.street_number2:
            street += " - " + partner.street_number2
        return {
            "nome": partner.legal_name or partner.name or "",
            "end": street or partner.street or "",
            "bairro": partner.district or "",
            "cidade": partner.city_id.name or partner.city or "",
            "uf": partner.state_id.code or "",
            "fone": partner.phone or "",
            "ie": partner.l10n_br_ie_code or "",
        }

    @api.model
    def _reprocess_cce_protocol_date(self, apply=False):
        """Fix the protocol_date of the correction letters stored before the
        dhRegEvento was converted to UTC (it kept the local time of Brasilia).

        Optional and never run by the module: it is called by hand, through
        scripts/reprocess_cce_protocol_date.py. Without apply (the default)
        nothing is written. The date is read again from the XML that was
        stored (the procEventoNFe, or the SOAP answer of the older letters),
        so running it twice changes nothing.

        :return: one line per letter: event, current, expected and the action
            ("ok", "fix", "fixed" or "skipped" with the reason).
        """
        events = self.search(
            [
                ("type", "=", "14"),
                ("state", "=", "done"),
                ("protocol_number", "!=", False),
            ],
            order="id",
        )
        report = []
        for event in events:
            line = {
                "event_id": event.id,
                "document_key": event.document_id.document_key,
                "sequence": event.sequence,
                "current": event.protocol_date
                and fields.Datetime.to_string(event.protocol_date),
                "expected": False,
            }
            registered = self._xml_values(
                event.file_response_id, "retEvento", event.protocol_number
            ).get("dhRegEvento")
            if not registered:
                line["action"] = "skipped (no dhRegEvento in the stored XML)"
            else:
                line["expected"] = self.env[
                    "l10n_br_fiscal.document"
                ]._event_registration_date(registered)
                if line["expected"] == line["current"]:
                    line["action"] = "ok"
                elif apply:
                    event.protocol_date = line["expected"]
                    line["action"] = "fixed"
                else:
                    line["action"] = "fix"
            report.append(line)
        return report
