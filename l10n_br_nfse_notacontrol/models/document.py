# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import random
from types import SimpleNamespace

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_REJEITADA,
)

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.assinatura.certificado import Certificado
    from erpbrasil.edoc.provedores.notacontrol import NS, NotaControl
except ImportError:  # pragma: no cover
    _logger.debug("erpbrasil.edoc without the NotaControl provider")

SIMULATED = "SIMULADO"


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
        cnpj = "".join(c for c in doc.company_id.cnpj_cpf or "" if c.isdigit())
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
    # keep the l10n_br_nfse_nacional behaviour. related=False: a redefined
    # field would otherwise keep the original related and ignore the compute.
    nfse10_nDPS = fields.Char(related=False, compute="_compute_nfse10_ndps")
    nfse10_Id = fields.Char(related=False, compute="_compute_nfse10_dps_id")

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
            registration = "".join(
                c for c in (rec.company_id.cnpj_cpf or "") if c.isalnum()
            ).upper()
            reg_type = "2" if len(registration) == 14 else "1"
            serie = "".join(c for c in (rec.document_serie or "") if c.isdigit())
            rec.nfse10_Id = (
                f"DPS{rec.company_id.city_id.ibge_code}{reg_type}"
                f"{registration.zfill(14)}{serie.zfill(5)}{str(number).zfill(15)}"
            )

    def _notacontrol_provider(self, session=None):
        self.ensure_one()
        company = self.company_id
        if not company.certificate:
            raise UserError(
                _("Configure the company A1 certificate to issue the NFS-e.")
            )
        if not company.inscr_mun:
            raise UserError(
                _(
                    "The NotaControl webservice requires the company municipal "
                    "registration (IM)."
                )
            )
        transmissao = SimpleNamespace(
            certificado=Certificado(
                company.certificate.file, company.certificate.password
            )
        )
        return NotaControl(
            transmissao,
            company.nfse_environment,
            int(company.city_id.ibge_code),
            company.cnpj_cpf,
            company.inscr_mun,
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
        dps_xml = self._notacontrol_adjust_dps(self.serialize()[0].to_xml())
        retorno = provider.recepcionar_lote_dps_sincrono([dps_xml], self.id)
        self._notacontrol_process_response(retorno, simulated=bool(session))

    @staticmethod
    def _notacontrol_adjust_dps(dps_xml):
        """NotaControl rule for a provider that is the issuer itself: send
        CNPJ/CPF, IM, contact and tax regime, but NOT name nor address."""
        if isinstance(dps_xml, str):
            dps_xml = dps_xml.encode("utf-8")
        root = etree.fromstring(dps_xml)
        prest = root.find(f".//{{{NS}}}prest")
        if prest is not None:
            for tag in ("xNome", "end", "NIF", "cNaoNIF"):
                for el in prest.findall(f"{{{NS}}}{tag}"):
                    prest.remove(el)
        return etree.tostring(root, encoding=str)

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
        message = retorno.mensagem or _("HTTP %s") % retorno.http_status
        code = (
            retorno.mensagens[0].codigo
            if retorno.mensagens
            else str(retorno.http_status)
        )
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
