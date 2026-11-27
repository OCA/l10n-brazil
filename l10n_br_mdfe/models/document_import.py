# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from erpbrasil.base.misc import punctuation_rm
from lxml import etree
from nfelib.mdfe.bindings.v3_0.mdfe_v3_00 import Mdfe
from nfelib.mdfe.bindings.v3_0.proc_mdfe_v3_00 import MdfeProc
from xsdata.exceptions import ParserError
from xsdata.formats.dataclass.parsers import XmlParser

from odoo import _, api, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_MDFE
from odoo.addons.l10n_br_fiscal_edi.tools import EDI_IMPORT_NO_CREATE, EdiParsedFile

MDFE_NAMESPACE = "http://www.portalfiscal.inf.br/mdfe"

# Roots of the MDF-e file that is authorized (mdfeProc) and of the one that is not.
MDFE_ROOTS = {"mdfeProc": MdfeProc, "MDFe": Mdfe}

PROTOCOL_AUTHORIZED = ("100", "132")
PROTOCOL_CANCELLED = ("101", "151", "155")


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    @api.model
    def _edi_import_read(self, name, content):
        try:
            root = etree.fromstring(
                content, etree.XMLParser(resolve_entities=False, no_network=True)
            )
        except etree.XMLSyntaxError:
            return super()._edi_import_read(name, content)
        tag = etree.QName(root)
        if tag.namespace != MDFE_NAMESPACE or tag.localname not in MDFE_ROOTS:
            return super()._edi_import_read(name, content)
        try:
            binding = XmlParser().from_bytes(content, MDFE_ROOTS[tag.localname])
        except ParserError:
            binding = None
        mdfe = getattr(binding, "MDFe", None) or binding
        infmdfe = getattr(mdfe, "infMDFe", None)
        if infmdfe is None or not re.fullmatch(r"MDFe\d{44}", infmdfe.Id or ""):
            raise UserError(_("The file %s is not a valid MDF-e.") % name)
        protocol = getattr(getattr(binding, "protMDFe", None), "infProt", None)
        status_code = str(protocol.cStat) if protocol is not None else ""
        emit = getattr(infmdfe, "emit", None)
        issuer = punctuation_rm(
            getattr(emit, "CNPJ", None) or getattr(emit, "CPF", None) or ""
        )
        return EdiParsedFile(
            reader="mdfe",
            document_type_code=MODELO_FISCAL_MDFE,
            access_key=infmdfe.Id[4:],
            issuer_vat=issuer,
            company_vats=(("issuer", issuer),) if issuer else (),
            status=self._mdfe_status(status_code),
            status_code=status_code,
            binding=binding,
            file_name=name,
            content=content,
        )

    @api.model
    def _mdfe_status(self, status_code):
        if status_code in PROTOCOL_AUTHORIZED:
            return "authorized"
        if status_code in PROTOCOL_CANCELLED:
            return "cancelled"
        return "unknown"

    @api.model
    def _edi_import_check(self, parsed, company):
        if (
            parsed.reader == "mdfe"
            and parsed.status == "unknown"
            and parsed.status_code
        ):
            raise UserError(
                _("This MDF-e is not authorized (status %s).") % parsed.status_code
            )
        return super()._edi_import_check(parsed, company)

    @api.model
    def _edi_import_create(self, parsed, company, role):
        if parsed.reader != "mdfe":
            return super()._edi_import_create(parsed, company, role)
        return self.import_binding_mdfe(parsed.binding, edoc_type="out")

    def _inverse_mdfe30_uf(self):
        """What the file declares is not written to the registry of the company."""
        if self.env.context.get(EDI_IMPORT_NO_CREATE):
            return None
        return super()._inverse_mdfe30_uf()
