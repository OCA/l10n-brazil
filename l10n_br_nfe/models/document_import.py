# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from xsdata.formats.dataclass.parsers import XmlParser

from odoo import _, api, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    MODELO_FISCAL_NFE,
)
from odoo.addons.l10n_br_fiscal_edi.tools import (
    EDI_IMPORT_NO_CREATE,
    EdiParsedFile,
    EdiPartnerData,
    tax_authority_date_to_utc,
)

PROTOCOL_AUTHORIZED = ("100", "150")
PROTOCOL_CANCELLED = ("101", "151", "155")
PROTOCOL_DENIED = ("110", "205", "301", "302", "303")


def _value(node):
    return getattr(node, "value", node)


def _inf_nfe(binding):
    """The ``infNFe`` of a binding, whether it is the ``nfeProc`` or the ``NFe``."""
    return getattr(getattr(binding, "NFe", binding), "infNFe", None)


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    @api.model
    def _edi_import_read(self, name, content):
        if b"infNFe" not in content:
            return super()._edi_import_read(name, content)
        try:
            binding = XmlParser().from_bytes(content)
        except Exception as error:  # pylint: disable=broad-except
            raise UserError(_("The file is not a valid NF-e XML.")) from error
        inf_nfe = _inf_nfe(binding)
        if inf_nfe is None:
            return super()._edi_import_read(name, content)
        if str(_value(inf_nfe.ide.mod)) != MODELO_FISCAL_NFE:
            raise UserError(_("Only NF-e (model 55) XML files can be imported."))
        protocol = getattr(binding, "protNFe", None)
        status_code = str(_value(protocol.infProt.cStat)) if protocol else ""
        recipient = inf_nfe.dest and (inf_nfe.dest.CNPJ or inf_nfe.dest.CPF)
        issuer = inf_nfe.emit.CNPJ or inf_nfe.emit.CPF
        return EdiParsedFile(
            reader="nfe",
            document_type_code=MODELO_FISCAL_NFE,
            access_key=inf_nfe.Id[3:],
            issuer_vat=issuer,
            company_vats=tuple(
                (role, vat)
                for role, vat in (("recipient", recipient), ("issuer", issuer))
                if vat
            ),
            status=self._nfe_import_status(status_code),
            status_code=status_code,
            binding=binding,
            file_name=name,
            content=content,
        )

    @api.model
    def _build_attr(self, node, fields, vals, path, attr):
        """The invoice (``fat``) of the collection is a mirror of fields that the
        document already has: its number (nFat) would renumber the document, and its
        original, discount and net values would overwrite the totals. What the file
        declares of the collection is read from the duplicates, not from here."""
        if self.env.context.get(EDI_IMPORT_NO_CREATE) and type(node).__name__ == "Fat":
            return False
        return super()._build_attr(node, fields, vals, path, attr)

    @api.model
    def _nfe_import_status(self, status_code):
        if status_code in PROTOCOL_AUTHORIZED:
            return "authorized"
        if status_code in PROTOCOL_CANCELLED:
            return "cancelled"
        if status_code in PROTOCOL_DENIED:
            return "denied"
        return "unknown"

    @api.model
    def _edi_import_check(self, parsed, company):
        if parsed.reader == "nfe" and parsed.status == "unknown" and parsed.status_code:
            raise UserError(
                _("This NF-e is not authorized (status %s).") % parsed.status_code
            )
        return super()._edi_import_check(parsed, company)

    @api.model
    def _edi_import_create(self, parsed, company, role):
        if parsed.reader != "nfe":
            return super()._edi_import_create(parsed, company, role)
        document = self.import_binding_nfe(
            parsed.binding, edoc_type="out" if role == "issuer" else "in"
        )
        document.partner_operation_name = _inf_nfe(parsed.binding).ide.natOp
        if role == "issuer":
            document._nfe_import_authorization(parsed)
        return document

    def _nfe_import_authorization(self, parsed):
        """The protocol of a note the company issued elsewhere: the number, the date
        and the file with the protocol are the ones the file carries. The event needs
        the series of the file; when the company has none with that code, the protocol
        goes to the history of the document instead."""
        protocol = getattr(parsed.binding, "protNFe", None)
        if protocol is None or parsed.status != "authorized":
            return
        inf_prot = protocol.infProt
        inf_nfe = _inf_nfe(parsed.binding)
        protocol_date = tax_authority_date_to_utc(inf_prot.dhRecbto)
        serie = self.env["l10n_br_fiscal.document.serie"].search(
            [
                ("code", "=", str(inf_nfe.ide.serie)),
                ("company_id", "=", self.company_id.id),
                ("document_type_id", "=", self.document_type_id.id),
            ],
            limit=1,
        )
        if not serie:
            self._message_log(
                body=_("Authorization protocol of the file: %(protocol)s, %(date)s.")
                % {"protocol": inf_prot.nProt, "date": protocol_date}
            )
            return
        production = str(_value(inf_nfe.ide.tpAmb)) == "1"
        event = self.env["l10n_br_fiscal.event"].create(
            {
                "company_id": self.company_id.id,
                "environment": EVENT_ENV_PROD if production else EVENT_ENV_HML,
                "type": "0",
                "document_id": self.id,
                "document_type_id": self.document_type_id.id,
                "document_serie_id": serie.id,
                "document_number": self.document_number,
            }
        )
        event.set_done(
            status_code=str(_value(inf_prot.cStat)),
            response=inf_prot.xMotivo,
            protocol_date=protocol_date,
            protocol_number=inf_prot.nProt,
            file_response_xml=parsed.content,
        )
        self.authorization_event_id = event

    @api.model
    def _edi_import_partner_hint(self, parsed):
        """The partner that the NF-e needs registered and the database lacks: the
        issuer of a note received, the recipient of one the company issued, and
        then the carrier, whichever is missing first."""
        if parsed.reader != "nfe":
            return super()._edi_import_partner_hint(parsed)
        inf_nfe = _inf_nfe(parsed.binding)
        companies = self.env["res.company"].sudo()
        issued_by_company = False
        for role, vat in parsed.company_vats:
            if companies.search_count([("partner_id.cnpj_cpf_stripped", "=", vat)]):
                issued_by_company = role == "issuer"
                break
        main = inf_nfe.dest if issued_by_company else inf_nfe.emit
        carrier = inf_nfe.transp and inf_nfe.transp.transporta
        partners = self.env["res.partner"].sudo().with_context(active_test=False)
        candidates = []
        for party in (main, carrier):
            vat = party and (party.CNPJ or party.CPF)
            if vat:
                candidates.append((party.xNome or "", vat))
        for name, vat in candidates:
            if not partners.search_count([("cnpj_cpf_stripped", "=", vat)]):
                return name, vat
        return candidates[0] if candidates else super()._edi_import_partner_hint(parsed)

    def _edi_import_partner_data(self, parsed):
        result = super()._edi_import_partner_data(parsed)
        if parsed.reader != "nfe":
            return result
        self.ensure_one()
        inf_nfe = _inf_nfe(parsed.binding)
        company_partner = self.company_id.partner_id
        issued = self.issuer == DOCUMENT_ISSUER_COMPANY
        parties = (
            (
                "issuer",
                inf_nfe.emit,
                inf_nfe.emit.enderEmit,
                company_partner if issued else self.partner_id,
            ),
            (
                "recipient",
                inf_nfe.dest,
                inf_nfe.dest and inf_nfe.dest.enderDest,
                self.partner_id if issued else company_partner,
            ),
        )
        for role, party, address, partner in parties:
            if party is None or partner == company_partner:
                # the registry of the company is its own, not the counterparty's
                continue
            result.append((partner, self._nfe_partner_data(role, party, address)))
        carrier = inf_nfe.transp and inf_nfe.transp.transporta
        if carrier is not None:
            result.append(
                (
                    self.nfe40_transporta,
                    EdiPartnerData(
                        role="carrier",
                        vat=carrier.CNPJ or carrier.CPF or "",
                        name=carrier.xNome or "",
                        state_tax_number=carrier.IE or "",
                        city=carrier.xMun or "",
                        state_code=str(_value(carrier.UF) or ""),
                    ),
                )
            )
        return result

    @api.model
    def _nfe_partner_data(self, role, party, address):
        return EdiPartnerData(
            role=role,
            vat=party.CNPJ or party.CPF or "",
            name=party.xNome or "",
            state_tax_number=party.IE or "",
            street=getattr(address, "xLgr", "") or "",
            street_number=getattr(address, "nro", "") or "",
            district=getattr(address, "xBairro", "") or "",
            zip_code=getattr(address, "CEP", "") or "",
            city=getattr(address, "xMun", "") or "",
            state_code=str(_value(getattr(address, "UF", "")) or ""),
        )
