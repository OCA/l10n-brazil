import base64
import gzip
import os
import re
import tempfile

import pytz
from nfelib import CommonMixin
from nfelib.nfse.bindings.v1_0.dps_v1_00 import Dps
from nfelib.nfse.bindings.v1_0.ped_reg_evento_v1_00 import PedRegEvento
from nfelib.nfse.bindings.v1_0.tipos_eventos_v1_00 import (
    TcinfPedReg,
    Te101101,
    Te101101XDesc,
)
from requests.exceptions import RequestException

from odoo import _, api, fields
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    MODELO_FISCAL_NFSE,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_REJEITADA,
)
from odoo.addons.spec_driven_model.models import spec_models

from ..constants.nfse_nacional import (
    ADN_BASE_URL,
    NFSE_NACIONAL_CANCEL_EVENT,
    NFSE_NACIONAL_CANCEL_OFICIO_EVENT,
)
from ..transport.adn_rest import AdnRestClient

BRAZIL_TZ = pytz.timezone("America/Sao_Paulo")


def filter_nfse_nacional(record):
    return (
        record.document_type_id and record.document_type_id.code == MODELO_FISCAL_NFSE
    )


class L10nBrFiscalDocument(spec_models.SpecModel):
    _name = "l10n_br_fiscal.document"
    _inherit = [
        "l10n_br_fiscal.document",
        #        "nfse.10.tcinfnfse",
        "nfse.10.tcdps",
        "nfse.10.tcinfdps",
    ]

    _nfse10_odoo_module = (
        "odoo.addons.l10n_br_nfse_spec.models.v1_0.tipos_complexos_v1_00"
    )
    _nfse10_binding_module = "nfelib.nfse.bindings.v1_0.tipos_complexos_v1_00"
    _nfse10_binding_type = "TcinfDps"  # Tcdps"
    #    _nfse10_binding_module = "nfelib.nfse.bindings.v1_0.dps_v1_00"
    #    _nfse10_binding_type = "Dps" #Tcdps"

    nfse10_infDPS = fields.Many2one(
        "l10n_br_fiscal.document", compute="_compute_nfse10_self"
    )

    nfse10_Id = fields.Char(compute="_compute_nfse10_id")
    nfse10_tpAmb = fields.Selection(related="company_id.nfse_environment")
    nfse10_dhEmi = fields.Char(compute="_compute_nfse10_dates")
    nfse10_verAplic = fields.Char(default="Odoo OCA")
    nfse10_serie = fields.Char(related="document_serie")
    nfse10_nDPS = fields.Char(related="document_number")
    nfse10_dCompet = fields.Char(compute="_compute_nfse10_dates")
    nfse10_tpEmit = fields.Selection(default="1")
    nfse10_cLocEmi = fields.Char(related="company_id.partner_id.city_id.ibge_code")

    nfse10_prest = fields.Many2one("res.company", related="company_id")
    nfse10_toma = fields.Many2one("res.partner", compute="_compute_nfse10_toma")
    nfse10_interm = fields.Many2one("res.partner")

    nfse10_serv = fields.Many2one(
        "l10n_br_fiscal.document.line", compute="_compute_nfse10_serv_valores"
    )
    nfse10_valores = fields.Many2one(
        "l10n_br_fiscal.document.line", compute="_compute_nfse10_serv_valores"
    )

    nfse_key = fields.Char(
        string="NFS-e Access Key", size=50, copy=False, readonly=True
    )
    nfse_number = fields.Char(string="NFS-e Number", copy=False, readonly=True)
    nfse_protocol = fields.Char(string="NFS-e Protocol", copy=False, readonly=True)
    edoc_error_message = fields.Text(readonly=True, copy=False)

    def _compute_nfse10_self(self):
        for rec in self:
            rec.nfse10_infDPS = rec.id

    @api.depends("partner_id.cnpj_cpf_stripped", "partner_id.nfse10_cNaoNIF")
    def _compute_nfse10_toma(self):
        for rec in self:
            partner = rec.partner_id
            identified = partner.cnpj_cpf_stripped or partner.nfse10_cNaoNIF
            rec.nfse10_toma = partner.id if identified else False

    @api.depends("document_key")
    def _compute_nfse10_id(self):
        for rec in self:
            rec.nfse10_Id = f"DPS{rec.document_key}" if rec.document_key else False

    @api.depends("document_date", "date_in_out")
    def _compute_nfse10_dates(self):
        for rec in self:
            if rec.document_date:
                local_dt = pytz.utc.localize(rec.document_date).astimezone(BRAZIL_TZ)
                rec.nfse10_dhEmi = local_dt.isoformat(timespec="seconds")
                rec.nfse10_dCompet = rec.document_date.strftime("%Y-%m-%d")
            else:
                rec.nfse10_dhEmi = False
                rec.nfse10_dCompet = False

    @api.depends("fiscal_line_ids")
    def _compute_nfse10_serv_valores(self):
        for rec in self:
            if rec.fiscal_line_ids:
                rec.nfse10_serv = rec.fiscal_line_ids[0].id
                rec.nfse10_valores = rec.fiscal_line_ids[0].id
            else:
                rec.nfse10_serv = False
                rec.nfse10_valores = False

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        if field_name == "nfse10_infDPS":
            return self._build_binding(
                class_name=class_obj._fields[field_name].comodel_name
            )
        return super()._export_many2one(field_name, xsd_required, class_obj)

    def import_binding_nfse(self, binding, edoc_type="in", dry_run=False):
        if hasattr(binding, "DPS"):
            binding = binding.DPS
        document = (
            self.env["nfse.10.tcdps"]
            .with_context(tracking_disable=True, edoc_type=edoc_type)
            .build_from_binding("nfse", "10", binding.infDPS, dry_run=dry_run)
        )
        return document

    @api.constrains("document_key")
    def _check_key(self):  # TODO required??
        """
        Bypass the 44-digit ChaveEdoc validation for NFS-e Nacional.
        DPS uses 42 digits and NFS-e uses 50 digits, which breaks the
        standard validation.
        """
        nfse_nacional_docs = self.filtered(
            lambda r: r.document_type_id
            and r.document_type_id.code == MODELO_FISCAL_NFSE
        )
        other_docs = self - nfse_nacional_docs

        # Only call the strict l10n_br_fiscal validation on NFe/CTe/MDFe
        if other_docs:
            return super(L10nBrFiscalDocument, other_docs)._check_key()

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.with_context(lang="pt_BR").filtered(filter_nfse_nacional):
            inf_dps = record._build_binding("nfse", "10")
            nfse = Dps(infDPS=inf_dps, versao="1.00", signature=None)
            edocs.append(nfse)
        return edocs

    def _document_export(self, pretty_print=True):
        result = super()._document_export()
        for record in self.filtered(filter_nfse_nacional):
            edoc = record.serialize()[0]
            xml_file = edoc.to_xml()
            if (
                record.authorization_event_id
                and record.authorization_event_id.state == "draft"
            ):
                record.sudo().authorization_event_id.unlink()
            event_id = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=record._nfse_nacional_event_env(),
                event_type="0",
                xml_file=xml_file,
                document_id=record,
            )
            record.authorization_event_id = event_id
            certificate = record.company_id.certificate
            signed_xml = edoc.sign_xml(
                xml_file, certificate.file, certificate.password, edoc.infDPS.Id
            )
            record._validate_xml(signed_xml)
        return result

    def _validate_xml(self, xml_file):
        self.ensure_one()
        if not self.filtered(filter_nfse_nacional):
            return super()._validate_xml(xml_file)
        erros = "\n".join(Dps.schema_validation(xml_file))
        self.write({"xml_error_message": erros or False})

    def _nfse_nacional_event_env(self):
        self.ensure_one()
        if self.company_id.nfse_environment == "1":
            return EVENT_ENV_PROD
        return EVENT_ENV_HML

    def _document_number(self):
        """Assign the DPS number and its access key.

        The shared implementation routes NFS-e numbering to ``rps_number``
        because municipal NFS-e is issued out of an RPS. NFS-e Nacional has
        no RPS: the number the issuer assigns is ``nDPS`` itself, and the
        DPS access key has 42 digits instead of the 44 of an NF-e.
        """
        result = super()._document_number()
        if not filter_nfse_nacional(self):
            return result
        if self.issuer != DOCUMENT_ISSUER_COMPANY:
            return result
        if not self.document_number and self.rps_number:
            self.document_number = self.rps_number
        if self.document_number and not self.document_key:
            self._nfse_nacional_generate_key()
        return result

    def _nfse_nacional_generate_key(self):
        """Build the 42 digit DPS key: city, issuer type, CNPJ/CPF,
        series and number."""
        self.ensure_one()
        partner = self.company_id.partner_id
        city_code = (partner.city_id.ibge_code or "").zfill(7)
        cnpj_cpf = re.sub(r"\D", "", partner.cnpj_cpf or "")
        issuer_type = "2" if len(cnpj_cpf) == 14 else "1"
        series = (self.document_serie or "").zfill(5)
        number = str(self.document_number or "").zfill(15)
        self.document_key = "".join(
            [city_code, issuer_type, cnpj_cpf.zfill(14), series, number]
        )

    def _eletronic_document_send(self):
        result = super()._eletronic_document_send()
        for record in self.filtered(filter_nfse_nacional):
            if record.xml_error_message:
                continue
            # l10n_br_fiscal_edi calls this hook from _after_document_send,
            # when the state machine already left "a_enviar" for "enviada",
            # so guarding on "a_enviar" would skip every transmission. Only
            # a document that already reached a final state is skipped.
            if record.state_edoc in (
                SITUACAO_EDOC_AUTORIZADA,
                SITUACAO_EDOC_CANCELADA,
            ):
                continue
            record._adn_send_for_authorization()
        return result

    def _adn_send_for_authorization(self):
        self.ensure_one()
        edoc = self.serialize()[0]
        certificate = self.company_id.certificate
        signed_xml = edoc.sign_xml(
            edoc.to_xml(), certificate.file, certificate.password, edoc.infDPS.Id
        )
        if not signed_xml.lstrip().startswith("<?xml"):
            signed_xml = '<?xml version="1.0" encoding="UTF-8"?>' + signed_xml
        packed = AdnRestClient.pack_dps(signed_xml)
        response = self._adn_post(lambda client: client.post_dps(packed))
        self._adn_process_response(response)

    def _adn_post(self, call):
        """Run ``call(client)`` against the ADN over mTLS with a temp 0600 PEM."""
        self.ensure_one()
        base_url = ADN_BASE_URL[self.company_id.nfse_environment]
        pem = self._adn_mtls_pem()
        tmp = tempfile.NamedTemporaryFile("wb", suffix=".pem", delete=False)
        try:
            os.chmod(tmp.name, 0o600)
            tmp.write(pem)
            tmp.close()
            client = AdnRestClient(base_url, tmp.name)
            try:
                return call(client)
            except RequestException as exc:
                raise UserError(
                    _(
                        "Could not reach the NFS-e Nacional service (ADN) at "
                        "%(url)s: %(err)s"
                    )
                    % {"url": base_url, "err": exc}
                ) from exc
        finally:
            os.unlink(tmp.name)

    def _adn_mtls_pem(self):
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            NoEncryption,
            PrivateFormat,
            pkcs12,
        )

        certificate = self.company_id.certificate
        pfx = base64.b64decode(certificate.file)
        password = (certificate.password or "").encode() or None
        key, cert, _extra = pkcs12.load_key_and_certificates(pfx, password)
        pem = key.private_bytes(
            Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()
        )
        pem += cert.public_bytes(Encoding.PEM)
        return pem

    def _adn_process_response(self, response):
        self.ensure_one()
        body = response.body or {}
        authorized = response.status_code in (200, 201) and bool(
            body.get("chaveAcesso")
        )
        if authorized:
            nfse_xml = self._adn_decode_nfse(body)
            self.write(
                {
                    "nfse_key": body.get("chaveAcesso"),
                    "nfse_number": body.get("nNFSe")
                    or body.get("numeroNfse")
                    or self._adn_xml_tag(nfse_xml, "nNFSe"),
                    "nfse_protocol": body.get("protocolo")
                    or body.get("nProt")
                    or self._adn_xml_tag(nfse_xml, "nDFSe"),
                    "status_code": str(body.get("status") or "100"),
                    "status_name": body.get("motivo") or _("Authorized"),
                    "edoc_error_message": False,
                }
            )
            self.authorization_event_id.set_done(
                status_code=self.status_code,
                response=self.status_name,
                protocol_date=fields.Datetime.now(),
                protocol_number=self.nfse_protocol,
                file_response_xml=nfse_xml,
            )
            self._change_state(SITUACAO_EDOC_AUTORIZADA)
        else:
            message = self._adn_format_errors(response)
            self.write(
                {
                    "edoc_error_message": message,
                    "status_code": str(response.status_code),
                    "status_name": _("Rejected"),
                }
            )
            self.authorization_event_id.set_done(
                status_code=str(response.status_code),
                response=message,
                protocol_date=fields.Datetime.now(),
                protocol_number=False,
                file_response_xml=False,
            )
            self.message_post(body=_("NFS-e rejected by the ADN:\n%s") % message)
            self._change_state(SITUACAO_EDOC_REJEITADA)

    @staticmethod
    def _adn_format_errors(response):
        body = response.body or {}
        erros = body.get("erros") or body.get("erro") or []
        lines = []
        for e in erros:
            code = e.get("Codigo") or e.get("codigo")
            desc = e.get("Descricao") or e.get("descricao")
            comp = e.get("complemento") or e.get("Complemento")
            lines.append(f"{code} - {desc}" + (f" ({comp})" if comp else ""))
        if lines:
            return "\n".join(lines)
        return body.get("mensagem") or response.content[:1000].decode(
            "utf-8", "replace"
        )

    @staticmethod
    def _adn_xml_tag(xml, tag):
        if not xml:
            return False
        match = re.search(rf"<{tag}>([^<]+)</{tag}>", xml)
        return match.group(1) if match else False

    @staticmethod
    def _adn_decode_nfse(body):
        raw = body.get("nfseXmlGZipB64")
        if raw:
            return gzip.decompress(base64.b64decode(raw)).decode("utf-8")
        return body.get("nfseXml") or ""

    def _document_cancel(self, justificative):
        for record in self.filtered(filter_nfse_nacional):
            motive = self.env.context.get("nfse_cancel_motive", "1")
            record._adn_cancel(justificative, motive)
        return super()._document_cancel(justificative)

    def _adn_cancel(self, justificative, motive):
        self.ensure_one()
        ped = self._build_cancel_pedreg(justificative, motive)
        certificate = self.company_id.certificate
        signed = CommonMixin.sign_xml(
            self._serialize_pedreg(ped),
            certificate.file,
            certificate.password,
            ped.infPedReg.Id,
        )
        if not signed.lstrip().startswith("<?xml"):
            signed = '<?xml version="1.0" encoding="UTF-8"?>' + signed
        packed = AdnRestClient.pack_dps(signed)
        response = self._adn_post(
            lambda client: client.post_event(self.nfse_key, packed)
        )
        return self._adn_process_cancel_response(response, signed)

    def _cancel_event_id(self):
        self.ensure_one()
        return f"PRE{self.nfse_key}{NFSE_NACIONAL_CANCEL_EVENT}"

    def _build_cancel_pedreg(self, justificative, motive):
        self.ensure_one()
        company = self.company_id
        cnpj = re.sub(r"\D", "", company.partner_id.cnpj_cpf or "")
        dt = (
            pytz.utc.localize(fields.Datetime.now())
            .astimezone(BRAZIL_TZ)
            .isoformat(timespec="seconds")
        )
        inf = TcinfPedReg(
            tpAmb=company.nfse_environment,
            verAplic="Odoo OCA",
            dhEvento=dt,
            CNPJAutor=cnpj,
            chNFSe=self.nfse_key,
            e101101=Te101101(
                xDesc=Te101101XDesc.CANCELAMENTO_DE_NFS_E,
                cMotivo=motive,
                xMotivo=justificative,
            ),
            Id=self._cancel_event_id(),
        )
        return PedRegEvento(infPedReg=inf, versao="1.00")

    @staticmethod
    def _serialize_pedreg(ped):
        from xsdata.formats.dataclass.serializers import XmlSerializer
        from xsdata.formats.dataclass.serializers.config import SerializerConfig

        serializer = XmlSerializer(config=SerializerConfig(pretty_print=False))
        return serializer.render(
            ped, ns_map={None: "http://www.sped.fazenda.gov.br/nfse"}
        )

    def _adn_process_cancel_response(self, response, signed_xml):
        self.ensure_one()
        if response.status_code not in (200, 201):
            raise UserError(
                _("NFS-e cancellation rejected by the ADN:\n%s")
                % self._adn_format_errors(response)
            )
        body = response.body or {}
        event = self.event_ids.create_event_save_xml(
            company_id=self.company_id,
            environment=self._nfse_nacional_event_env(),
            event_type="2",
            xml_file=signed_xml,
            document_id=self,
        )
        self.cancel_event_id = event
        event.set_done(
            status_code=str(response.status_code),
            response=body.get("mensagem") or _("Cancelled"),
            protocol_date=fields.Datetime.now(),
            protocol_number=body.get("protocolo") or body.get("nProt") or False,
            file_response_xml=self._adn_decode_nfse(body) or signed_xml,
        )
        return True

    def action_adn_check_status(self):
        for record in self.filtered(filter_nfse_nacional):
            record._adn_check_cancellation_status()

    def _adn_check_cancellation_status(self):
        self.ensure_one()
        if self.state_edoc != SITUACAO_EDOC_AUTORIZADA:
            return
        for event_type in (
            NFSE_NACIONAL_CANCEL_EVENT,
            NFSE_NACIONAL_CANCEL_OFICIO_EVENT,
        ):
            response = self._adn_post(
                lambda client, et=event_type: client.get_event(self.nfse_key, et, "1")
            )
            if response.status_code in (200, 201):
                self._adn_register_external_cancellation(event_type, response)
                return

    def _adn_register_external_cancellation(self, event_type, response):
        self.ensure_one()
        body = response.body or {}
        raw = body.get("eventoXmlGZipB64")
        xml = gzip.decompress(base64.b64decode(raw)).decode("utf-8") if raw else ""
        event = self.event_ids.create_event_save_xml(
            company_id=self.company_id,
            environment=self._nfse_nacional_event_env(),
            event_type="2",
            xml_file=xml,
            document_id=self,
        )
        self.cancel_event_id = event
        event.set_done(
            status_code=event_type,
            response=_("Cancelled at the ADN by another means (event %s)") % event_type,
            protocol_date=fields.Datetime.now(),
            protocol_number=False,
            file_response_xml=xml,
        )
        self.message_post(
            body=_(
                "NFS-e was cancelled directly at the ADN (event %s), "
                "detected via status check."
            )
            % event_type
        )
        self._change_state(SITUACAO_EDOC_CANCELADA)

    def make_pdf(self):
        nacional_docs = self.filtered(filter_nfse_nacional)
        if not nacional_docs:
            return super().make_pdf()
        report = self.env.ref("l10n_br_nfse_nacional.report_danfse_nacional")
        for record in nacional_docs:
            pdf = report._render_qweb_pdf(report.id, record.ids)[0]
            vals = {
                "name": f"DANFSe-{record.document_number or record.id}.pdf",
                "res_model": record._name,
                "res_id": record.id,
                "datas": base64.b64encode(pdf),
                "mimetype": "application/pdf",
                "type": "binary",
            }
            if record.file_report_id:
                record.file_report_id.write(vals)
            else:
                record.file_report_id = self.env["ir.attachment"].create(vals)
        remaining = self - nacional_docs
        if remaining:
            return super(L10nBrFiscalDocument, remaining).make_pdf()
