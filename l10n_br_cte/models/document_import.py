# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from erpbrasil.base.fiscal.cnpj_cpf import formata
from erpbrasil.base.misc import punctuation_rm
from lxml import etree
from nfelib.cte.bindings.v4_0.cte_v4_00 import Cte
from nfelib.cte.bindings.v4_0.proc_cte_v4_00 import CteProc
from xsdata.exceptions import ParserError
from xsdata.formats.dataclass.parsers import XmlParser

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_CTE
from odoo.addons.l10n_br_fiscal_edi.tools import EdiParsedFile, EdiPartnerData

CTE_NAMESPACE = "http://www.portalfiscal.inf.br/cte"

# Roots of the CT-e file that is authorized (cteProc) and of the one that is not.
CTE_ROOTS = {"cteProc": CteProc, "CTe": Cte}

# Other documents of the same namespace that are not a CT-e (model 57).
NOT_IMPORTABLE_ROOTS = {
    "cteOSProc": "CT-e OS",
    "CTeOS": "CT-e OS",
    "GTVeProc": "GTV-e",
    "GTVe": "GTV-e",
    "cteSimpProc": "CT-e Simp",
    "CTeSimp": "CT-e Simp",
}

PROTOCOL_AUTHORIZED = ("100", "150")
PROTOCOL_CANCELLED = ("101", "151", "155")
PROTOCOL_DENIED = ("110", "205", "301", "302", "303")

# toma3/toma: which party of the CT-e takes the service.
TAKER_BY_CODE = {"0": "rem", "1": "exped", "2": "receb", "3": "dest"}


def _value(node):
    return getattr(node, "value", node)


def _vat(party):
    """Digits of the CNPJ or CPF of a party of the CT-e, or False."""
    if party is None:
        return False
    return punctuation_rm(getattr(party, "CNPJ", None) or getattr(party, "CPF", None))


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    cte_company_role = fields.Selection(
        [
            ("taker", "Taker"),
            ("other", "Sender, recipient, shipper or receiver"),
        ],
        string="Role of the Company in the CT-e",
        readonly=True,
        copy=False,
        help="What the company is in a CT-e that it received: the taker of the "
        "freight, who owes it, or one of the other parties, for whom the CT-e is "
        "only registered.",
    )

    def _edi_no_payable_reason(self):
        if self.cte_company_role == "other":
            return _(
                "The company is not the taker of this CT-e: it stays registered, "
                "with no amount to pay."
            )
        return super()._edi_no_payable_reason()

    @api.model
    def _edi_import_read(self, name, content):
        try:
            root = etree.fromstring(
                content, etree.XMLParser(resolve_entities=False, no_network=True)
            )
        except etree.XMLSyntaxError:
            return super()._edi_import_read(name, content)
        tag = etree.QName(root)
        if tag.namespace != CTE_NAMESPACE:
            return super()._edi_import_read(name, content)
        if tag.localname in NOT_IMPORTABLE_ROOTS:
            raise UserError(
                _(
                    "Only the CT-e (model 57) can be imported as a fiscal document. "
                    "The file %(name)s is a %(kind)s.",
                    name=name,
                    kind=NOT_IMPORTABLE_ROOTS[tag.localname],
                )
            )
        if tag.localname not in CTE_ROOTS:
            return super()._edi_import_read(name, content)
        try:
            binding = XmlParser().from_bytes(content, CTE_ROOTS[tag.localname])
        except ParserError:
            binding = None
        cte = getattr(binding, "CTe", None) or binding
        infcte = getattr(cte, "infCte", None)
        if infcte is None or not re.fullmatch(r"CTe\d{44}", infcte.Id or ""):
            raise UserError(_("The file %s is not a valid CT-e.") % name)
        protocol = getattr(getattr(binding, "protCTe", None), "infProt", None)
        status_code = str(protocol.cStat) if protocol is not None else ""
        return EdiParsedFile(
            reader="cte",
            document_type_code=MODELO_FISCAL_CTE,
            access_key=infcte.Id[3:],
            issuer_vat=_vat(infcte.emit),
            company_vats=self._cte_company_vats(infcte),
            status=self._cte_status(status_code),
            status_code=status_code,
            binding=binding,
            file_name=name,
            content=content,
        )

    @api.model
    def _cte_company_vats(self, infcte):
        """Who may be the company, in order: the taker of the service, the
        recipient, the sender, the shipper, the receiver and the issuer. A CT-e in
        which the company is the issuer and also the taker (own transport) enters
        as the taker. Any party that is not the taker has the role ``recipient``:
        the CT-e is registered for it, with no amount to pay."""
        vats = [
            ("taker", _vat(self._cte_taker(infcte))),
            ("recipient", _vat(getattr(infcte, "dest", None))),
            ("recipient", _vat(getattr(infcte, "rem", None))),
            ("recipient", _vat(getattr(infcte, "exped", None))),
            ("recipient", _vat(getattr(infcte, "receb", None))),
            ("issuer", _vat(getattr(infcte, "emit", None))),
        ]
        return tuple((role, vat) for role, vat in vats if vat)

    @api.model
    def _cte_taker(self, infcte):
        """The party of the CT-e that takes the service."""
        ide = infcte.ide
        if getattr(ide, "toma3", None) is not None:
            code = TAKER_BY_CODE.get(str(_value(ide.toma3.toma)))
            return getattr(infcte, code, None) if code else None
        return getattr(ide, "toma4", None)

    @api.model
    def _cte_taker_partner(self, infcte):
        """The partner of a CT-e issued by the company is its taker, as in a CT-e
        that the company issues: found by the CNPJ or created from the file."""
        taker = self._cte_taker(infcte)
        digits = _vat(taker)
        if not digits:
            return self.env["res.partner"]
        partner = self.env["res.partner"].search(
            [("cnpj_cpf_stripped", "=", digits)], limit=1
        )
        return partner or self.env["res.partner"].create(
            {
                "name": taker.xNome,
                "legal_name": taker.xNome,
                "vat": formata(digits),
                "is_company": len(digits) == 14,
                "company_type": "company" if len(digits) == 14 else "person",
                "country_id": self.env.ref("base.br").id,
            }
        )

    @api.model
    def _cte_suggest_product(self, document, company, issued=False):
        """The default product of the company, when the user can see it, goes to the
        line of the CT-e, which takes the unit of the product: the review then finds
        a suggestion to confirm. It is the freight product for a CT-e that the
        company received and the transport service provided for one that it issued.
        Nothing is created."""
        default = (
            company.cte_import_service_product_id
            if issued
            else company.cte_import_product_id
        )
        product = self.env["product.product"].search([("id", "=", default.id)])
        if product:
            document.fiscal_line_ids.product_id = product

    @api.model
    def _edi_import_partner_hint(self, parsed):
        """The emitter of a CT-e that the company receives, the taker of one that it
        issued: the partner that the document needs registered."""
        if parsed.reader != "cte":
            return super()._edi_import_partner_hint(parsed)
        try:
            _company, role = self._edi_import_company(parsed)
        except UserError:
            role = False
        cte = getattr(parsed.binding, "CTe", None) or parsed.binding
        party = self._cte_taker(cte.infCte) if role == "issuer" else cte.infCte.emit
        return party.xNome or "", _vat(party)

    def _edi_import_partner_data(self, parsed):
        """What the CT-e declares about the emitter, the sender, the recipient and the
        taker, with the partner of the registry that has the same CNPJ or CPF."""
        result = super()._edi_import_partner_data(parsed)
        if parsed.reader != "cte":
            return result
        cte = getattr(parsed.binding, "CTe", None) or parsed.binding
        infcte = cte.infCte
        taker = self._cte_taker(infcte)
        for role, party, address in (
            ("issuer", infcte.emit, "enderEmit"),
            ("sender", getattr(infcte, "rem", None), "enderReme"),
            ("recipient", getattr(infcte, "dest", None), "enderDest"),
            ("taker", taker, "enderToma"),
        ):
            if party is None:
                continue
            address = getattr(party, address, None) or self._cte_taker_address(
                infcte, party
            )
            result.append(self._cte_partner_data(role, party, address))
        return result

    @api.model
    def _cte_taker_address(self, infcte, party):
        """The address of a taker that is one of the parties of the CT-e (toma3)."""
        for name, address in (
            ("rem", "enderReme"),
            ("exped", "enderExped"),
            ("receb", "enderReceb"),
            ("dest", "enderDest"),
        ):
            if getattr(infcte, name, None) is party:
                return getattr(party, address, None)
        return None

    def _cte_partner_data(self, role, party, address):
        vat = _vat(party) or ""
        partner = self.env["res.partner"]
        if vat:
            partner = partner.search([("cnpj_cpf_stripped", "=", vat)], limit=1)
        city = getattr(address, "xMun", None) or ""
        state = _value(getattr(address, "UF", None)) or ""
        return partner, EdiPartnerData(
            role=role,
            vat=vat,
            name=party.xNome or "",
            state_tax_number=getattr(party, "IE", None) or "",
            street=getattr(address, "xLgr", None) or "",
            street_number=getattr(address, "nro", None) or "",
            district=getattr(address, "xBairro", None) or "",
            zip_code=getattr(address, "CEP", None) or "",
            city=city,
            state_code=str(state),
        )

    @api.model
    def _cte_status(self, status_code):
        if status_code in PROTOCOL_AUTHORIZED:
            return "authorized"
        if status_code in PROTOCOL_CANCELLED:
            return "cancelled"
        if status_code in PROTOCOL_DENIED:
            return "denied"
        return "unknown"

    @api.model
    def _edi_import_check(self, parsed, company):
        if parsed.reader == "cte" and parsed.status == "unknown" and parsed.status_code:
            raise UserError(
                _("This CT-e is not authorized (status %s).") % parsed.status_code
            )
        return super()._edi_import_check(parsed, company)

    @api.model
    def _edi_import_create(self, parsed, company, role):
        if parsed.reader != "cte":
            return super()._edi_import_create(parsed, company, role)
        issued = role == "issuer"
        document = self.import_binding_cte(
            parsed.binding, edoc_type="out" if issued else "in"
        )
        cte = getattr(parsed.binding, "CTe", None) or parsed.binding
        if issued:
            document.partner_id = self._cte_taker_partner(cte.infCte)
        else:
            document.cte_company_role = "taker" if role == "taker" else "other"
        self._cte_suggest_product(document, company, issued=issued)
        document.partner_operation_name = cte.infCte.ide.natOp
        for line in document.fiscal_line_ids:
            line.partner_cfop_id = line.cfop_id
        return document
