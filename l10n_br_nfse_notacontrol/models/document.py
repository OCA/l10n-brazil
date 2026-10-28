# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import random
from types import SimpleNamespace

import pytz
from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_REJEITADA,
)
from odoo.addons.l10n_br_nfse_nacional.models.document import BRAZIL_TZ

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.edoc.provedores.notacontrol import NS, NotaControl
except ImportError:  # pragma: no cover
    _logger.debug("erpbrasil.edoc without the NotaControl provider")

SIMULATED = "SIMULADO"

# DPS 1.01 (NotaControl layout of Goiania, schema_v101.xsd)
DPS_VERSION = "1.01"
# tpRetPisCofins: 1.00 had 1 (retained) / 2 (not retained); 1.01 splits
# PIS/COFINS/CSLL: 3 = all retained, 0 = none retained
TP_RET_PIS_COFINS_101 = {"1": "3", "2": "0"}
# IBSCBS group as in the NFS-e the city portal issues (DPS 1.01): regular
# NFS-e, service operation indicator, the taker is the recipient, CST 000 /
# cClassTrib 000001 (full taxation, no IBS/CBS value in 2026). Only used when
# l10n_br_nfse_nacional did not export the group (line without RTC data).
IBSCBS_DEFAULT = {
    "finNFSe": "0",
    "cIndOp": "050101",
    "indDest": "0",
    "CST": "000",
    "cClassTrib": "000001",
}


class _SimulatedResponse:
    def __init__(self, content):
        self.content = content.encode("utf-8")
        self.status_code = 200


class _SimulatedSession:
    """Answers like the NotaControl webservice without transmitting anything.

    Rehearsal only (company flag nfse_notacontrol_simulated): the DPS is
    signed and packed exactly as it would be sent; the authorization that
    comes back is made up and flagged as SIMULADO everywhere.
    """

    def __init__(self, document):
        self.document = document
        self.sent = None

    def post(self, url, data, headers, timeout):
        self.sent = data.decode("utf-8")
        doc = self.document
        now = fields.Datetime.context_timestamp(doc, fields.Datetime.now())
        cnpj = doc.company_id.partner_id.cnpj_cpf_stripped or ""
        number = str(doc.rps_number or doc.document_number or doc.id).zfill(13)
        # 50-position key: city, issuing environment, registration type,
        # CNPJ, number, YYMM, random code and check digit
        key = (
            f"{doc.company_id.city_id.ibge_code}21{cnpj}{number}"
            f"{now:%y%m}{random.randint(0, 10**9 - 1):09d}"
        )
        key += str(sum(int(c) for c in key) % 10)
        body = (
            f'<EnviarLoteDpsSincronoResposta xmlns="{NS}">'
            f"<NumeroLote>{doc.id}</NumeroLote>"
            f"<DataRecebimento>{now:%Y-%m-%dT%H:%M:%S}</DataRecebimento>"
            f"<Protocolo>{SIMULATED}-{doc.id}</Protocolo>"
            "<ListaNfse><CompNfse>"
            f'<Nfse versao="1.01"><infNFSe Id="NFS{key}">'
            f"<xLocEmi>{doc.company_id.city_id.name}</xLocEmi>"
            f"<nNFSe>{int(number)}</nNFSe><cStat>100</cStat>"
            f"<dhProc>{now:%Y-%m-%dT%H:%M:%S}-03:00</dhProc>"
            f"<xOutInf>NFS-e {SIMULATED}: nao transmitida</xOutInf>"
            "</infNFSe></Nfse>"
            "</CompNfse></ListaNfse></EnviarLoteDpsSincronoResposta>"
        )
        return _SimulatedResponse(body)


class L10nBrFiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    # For NotaControl companies the DPS follows the national layout strictly:
    # the NFS-e workflow numbers the RPS (rps_number), not document_number,
    # and the DPS Id has its own 45-position layout (TSIdDPS). Other companies
    # keep the l10n_br_nfse_nacional behaviour. related=None: a redefined
    # field would otherwise keep the original related and ignore the compute
    # (None and not False: the spec_driven_model import reads field.related).
    nfse10_nDPS = fields.Char(related=None, compute="_compute_nfse10_ndps")
    nfse10_Id = fields.Char(related=None, compute="_compute_nfse10_dps_id")

    @api.model
    def _prepare_import_dict(
        self, vals, model=None, parent_dict=None, defaults_model=False
    ):
        # Without the related, the import no longer maps nDPS back to the
        # document number.
        if vals.get("nfse10_nDPS") and not vals.get("document_number"):
            vals["document_number"] = vals["nfse10_nDPS"]
        return super()._prepare_import_dict(
            vals, model=model, parent_dict=parent_dict, defaults_model=defaults_model
        )

    @api.depends("rps_number", "document_number", "company_id")
    def _compute_nfse10_ndps(self):
        for rec in self:
            number = rec.document_number
            if rec.company_id.nfse_notacontrol:
                number = rec.rps_number or rec.document_number
                if number and number.isdigit():
                    number = str(int(number))
            rec.nfse10_nDPS = number

    @api.depends(
        "document_key", "rps_number", "document_number", "document_serie", "company_id"
    )
    def _compute_nfse10_dps_id(self):
        """TSIdDPS: DPS + city (7) + registration type (1) + CNPJ/CPF (14,
        CPF left-padded with zeros) + series (5) + number (15)."""
        for rec in self:
            if not rec.company_id.nfse_notacontrol:
                rec.nfse10_Id = f"DPS{rec.document_key}" if rec.document_key else False
                continue
            number = rec.rps_number or rec.document_number
            if not number or not rec.company_id.city_id.ibge_code:
                rec.nfse10_Id = False
                continue
            partner = rec.company_id.partner_id
            registration = (partner.cnpj_cpf_stripped or "").upper()
            reg_type = "2" if len(registration) == 14 else "1"
            serie = "".join(c for c in (rec.document_serie or "") if c.isdigit())
            rec.nfse10_Id = (
                f"DPS{rec.company_id.city_id.ibge_code}{reg_type}"
                f"{registration.zfill(14)}{serie.zfill(5)}{str(number).zfill(15)}"
            )

    def _compute_nfse10_dates(self):
        """l10n_br_nfse_nacional already labels dhEmi in Brazilian local time,
        but takes dCompet from the UTC date: after 21:00 the DPS would be
        competent on the next day, after its own emission."""
        res = super()._compute_nfse10_dates()
        for rec in self.filtered(
            lambda r: r.company_id.nfse_notacontrol and r.document_date
        ):
            local = pytz.utc.localize(rec.document_date).astimezone(BRAZIL_TZ)
            rec.nfse10_dCompet = local.strftime("%Y-%m-%d")
        return res

    def _notacontrol_provider(self, session=None):
        self.ensure_one()
        company = self.company_id
        if not company.l10n_br_im_code:
            raise UserError(
                _(
                    "The NotaControl webservice requires the company municipal "
                    "registration (IM)."
                )
            )
        # raises when the company has no valid A1 certificate
        transmissao = SimpleNamespace(certificado=company._get_br_ecertificate())
        return NotaControl(
            transmissao,
            company.nfse_environment,
            int(company.city_id.ibge_code),
            company.partner_id.cnpj_cpf_stripped,
            company.l10n_br_im_code,
            algoritmo=company.nfse_notacontrol_algorithm or "sha1",
            session=session,
        )

    def _adn_send_for_authorization(self):
        self.ensure_one()
        if not self.company_id.nfse_notacontrol:
            return super()._adn_send_for_authorization()
        session = None
        if self.company_id.nfse_notacontrol_simulated:
            session = _SimulatedSession(self)
        provider = self._notacontrol_provider(session=session)
        city_code = self.fiscal_line_ids.city_taxation_code_id[:1].code
        dps_xml = self._notacontrol_adjust_dps(
            self.serialize()[0].to_xml(), city_taxation_code=city_code
        )
        retorno = provider.recepcionar_lote_dps_sincrono([dps_xml], self.id)
        self._notacontrol_process_response(retorno, simulated=bool(session))

    @staticmethod
    def _notacontrol_adjust_dps(dps_xml, city_taxation_code=None):
        """NotaControl rule for a provider that is the issuer itself: send
        CNPJ/CPF, IM, contact and tax regime, but NOT name nor address.
        The municipal taxation code goes right after cTribNac, unmasked."""
        if isinstance(dps_xml, str):
            dps_xml = dps_xml.encode("utf-8")
        root = etree.fromstring(dps_xml)
        prest = root.find(f".//{{{NS}}}prest")
        if prest is not None:
            for tag in ("xNome", "end", "NIF", "cNaoNIF"):
                for el in prest.findall(f"{{{NS}}}{tag}"):
                    prest.remove(el)
        code = "".join(c for c in city_taxation_code or "" if c.isdigit())
        ctribnac = root.find(f".//{{{NS}}}cServ/{{{NS}}}cTribNac")
        if code and ctribnac is not None:
            for old in ctribnac.getparent().findall(f"{{{NS}}}cTribMun"):
                old.getparent().remove(old)
            el = etree.Element(f"{{{NS}}}cTribMun")
            el.text = code
            ctribnac.addnext(el)
        L10nBrFiscalDocument._notacontrol_dps_101(root)
        return etree.tostring(root, encoding=str)

    @staticmethod
    def _notacontrol_dps_101(root):
        """The NotaControl batch is 1.01 and refuses (E160) a DPS 1.00: raise
        the version, drop empty groups left by the binding, map
        tpRetPisCofins to the 1.01 domain, keep pAliq after tpRetISSQN and add
        the IBSCBS group when l10n_br_nfse_nacional did not export it."""
        root.set("versao", DPS_VERSION)
        changed = True
        while changed:  # an emptied parent may become empty too
            changed = False
            for el in list(root.iter()):
                if el is root or not isinstance(el.tag, str):
                    continue
                if len(el) == 0 and not (el.text or "").strip() and not el.attrib:
                    el.getparent().remove(el)
                    changed = True
        for el in root.iter(f"{{{NS}}}tpRetPisCofins"):
            el.text = TP_RET_PIS_COFINS_101.get(el.text, el.text)
        for trib_mun in root.iter(f"{{{NS}}}tribMun"):
            aliq = trib_mun.find(f"{{{NS}}}pAliq")
            ret = trib_mun.find(f"{{{NS}}}tpRetISSQN")
            if aliq is not None and ret is not None:
                ret.addnext(aliq)
        inf = root.find(f"{{{NS}}}infDPS")
        if inf is None or inf.find(f"{{{NS}}}IBSCBS") is not None:
            return

        def sub(parent, tag, text=None):
            el = etree.SubElement(parent, f"{{{NS}}}{tag}")
            el.text = text
            return el

        ibscbs = sub(inf, "IBSCBS")
        for tag in ("finNFSe", "cIndOp", "indDest"):
            sub(ibscbs, tag, IBSCBS_DEFAULT[tag])
        g = sub(sub(sub(ibscbs, "valores"), "trib"), "gIBSCBS")
        sub(g, "CST", IBSCBS_DEFAULT["CST"])
        sub(g, "cClassTrib", IBSCBS_DEFAULT["cClassTrib"])

    def _notacontrol_authorization_event(self, retorno):
        """The event is normally created at confirmation (_document_export);
        a direct send must still leave the request XML on record."""
        self.ensure_one()
        if not self.authorization_event_id:
            self.authorization_event_id = self.event_ids.create_event_save_xml(
                company_id=self.company_id,
                environment=self._nfse_nacional_event_env(),
                event_type="0",
                xml_file=retorno.xml_enviado,
                document_id=self,
            )
        return self.authorization_event_id

    def _notacontrol_process_response(self, retorno, simulated=False):
        self.ensure_one()
        event = self._notacontrol_authorization_event(retorno)
        label = f" ({SIMULATED})" if simulated else ""
        if retorno.sucesso:
            self.write(
                {
                    "nfse_key": retorno.chaves_acesso[0],
                    "nfse_number": retorno.numeros_nfse[0],
                    "nfse_protocol": retorno.protocolo,
                    "status_code": "100",
                    "status_name": _("Authorized") + label,
                    "edoc_error_message": False,
                }
            )
            event.set_done(
                status_code="100",
                response=_("Authorized by NotaControl") + label,
                protocol_date=fields.Datetime.now(),
                protocol_number=retorno.protocolo,
                file_response_xml=retorno.nfse_xml[0],
            )
            self._change_state(SITUACAO_EDOC_AUTORIZADA)
            if simulated:
                self.message_post(
                    body=_(
                        "NFS-e %(label)s: the DPS was signed and packed for "
                        "NotaControl, but NOTHING was transmitted. Number and "
                        "key are made up for rehearsal."
                    )
                    % {"label": SIMULATED}
                )
            return
        mensagens = retorno.mensagens or self._notacontrol_response_messages(
            retorno.xml_resposta
        )
        message = "\n".join(
            " - ".join(p for p in (m.codigo, m.mensagem, m.correcao) if p)
            for m in mensagens
        ) or (_("HTTP %s") % retorno.http_status)
        code = mensagens[0].codigo if mensagens else str(retorno.http_status)
        self.write(
            {
                "edoc_error_message": message,
                "status_code": code,
                "status_name": _("Rejected"),
            }
        )
        event.set_done(
            status_code=self.status_code,
            response=message,
            protocol_date=fields.Datetime.now(),
            protocol_number=False,
            file_response_xml=retorno.xml_resposta or False,
        )
        self.message_post(body=_("NFS-e rejected by NotaControl:\n%s") % message)
        self._change_state(SITUACAO_EDOC_REJEITADA)

    @staticmethod
    def _notacontrol_response_messages(xml_resposta):
        """The provider misses ListaMensagemRetorno when the answer comes as
        RecepcionarLoteDpsSincronoResponse/EnviarLoteDpsSincronoResposta
        (no *Result wrapper): read it here so the rejection shows its code."""
        if not xml_resposta:
            return []
        if isinstance(xml_resposta, bytes):
            xml_resposta = xml_resposta.decode("utf-8", "replace")
        xml_resposta = xml_resposta.lstrip("\ufeff").strip()
        try:
            doc = etree.fromstring(xml_resposta.encode("utf-8"))
        except etree.XMLSyntaxError:
            return []
        return [
            SimpleNamespace(
                codigo=m.findtext(f"{{{NS}}}Codigo") or "",
                mensagem=m.findtext(f"{{{NS}}}Mensagem") or "",
                correcao=m.findtext(f"{{{NS}}}Correcao") or "",
            )
            for m in doc.iter(f"{{{NS}}}MensagemRetorno")
        ]

    def _adn_cancel(self, justificative, motive):
        self.ensure_one()
        if not self.company_id.nfse_notacontrol:
            return super()._adn_cancel(justificative, motive)
        if self.company_id.nfse_notacontrol_simulated:
            raise UserError(
                _(
                    "Cancellation is not simulated: configure the certificate "
                    "and the homologation environment."
                )
            )
        ped = self._build_cancel_pedreg(justificative, motive)
        retorno = self._notacontrol_provider().cancelar_nfse(
            self._serialize_pedreg(ped)
        )
        if not retorno.sucesso:
            raise UserError(
                _("NFS-e cancellation rejected by NotaControl:\n%s") % retorno.mensagem
            )
        event = self.event_ids.create_event_save_xml(
            company_id=self.company_id,
            environment=self._nfse_nacional_event_env(),
            event_type="2",
            xml_file=retorno.xml_enviado,
            document_id=self,
        )
        self.cancel_event_id = event
        event.set_done(
            status_code="100",
            response=_("Cancelled"),
            protocol_date=fields.Datetime.now(),
            protocol_number=retorno.protocolo or False,
            file_response_xml=retorno.xml_resposta,
        )
        return True
