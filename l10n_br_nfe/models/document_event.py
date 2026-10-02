# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import EVENT_ENV_HML

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
        if root.tag != "{%s}procEventoNFe" % NFE_XML_NAMESPACE["nfe"]:
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
        """Issuer data of the DACCE header (the keys that the library reads)."""
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
        }

    def _is_homologation(self):
        self.ensure_one()
        return self.environment == EVENT_ENV_HML
