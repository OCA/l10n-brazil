# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

from .transmissao import SUFIXO, TransmissaoMock, proc_generico

_logger = logging.getLogger(__name__)

NFE, NFCE, CTE, MDFE = "55", "65", "57", "58"
GENERICOS = {
    # modelo: (raiz do processo, raiz do protocolo, namespace, motivo,
    # campo de ambiente)
    CTE: (
        "cteProc",
        "protCTe",
        "http://www.portalfiscal.inf.br/cte",
        "Autorizado o uso do CT-e",
        "cte_environment",
    ),
    MDFE: (
        "mdfeProc",
        "protMDFe",
        "http://www.portalfiscal.inf.br/mdfe",
        "Autorizado o uso do MDF-e",
        "mdfe_environment",
    ),
}


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    edoc_mock_mode = fields.Boolean(related="company_id.edoc_mock_mode")

    def _edoc_mock_check(self, ambiente):
        self.ensure_one()
        if ambiente != "2":
            raise UserError(
                _(
                    "SEFAZ simulada so pode ser usada em ambiente de homologacao. "
                    "Desligue o modo simulado da empresa para emitir em producao."
                )
            )

    def _edoc_processor(self):
        processador = super()._edoc_processor()
        if (
            len(self) == 1
            and self.company_id.edoc_mock_mode
            and self.document_type in (NFE, NFCE)
            and processador is not None
        ):
            self._edoc_mock_check(self.nfe_environment)
            if not hasattr(processador, "_transmissao"):
                # transmissao pelo cliente da nfelib (parametro de sistema
                # l10n_br_nfe.nfelib_soap_transmission = True): ainda nao simulada
                raise UserError(
                    _(
                        "SEFAZ simulada: a transmissao pelo cliente da nfelib "
                        "ainda nao e simulada. Desligue o parametro de sistema "
                        "l10n_br_nfe.nfelib_soap_transmission para usar a "
                        "erpbrasil.edoc."
                    )
                )
            _logger.info("SEFAZ simulada: %s %s", self.document_type, self.document_key)
            processador._transmissao = TransmissaoMock(
                self.company_id.state_id.ibge_code,
                self.nfe_environment,
                certificado=processador._transmissao.certificado,
            )
            # resposta sincrona: o protocolo volta junto com o envio do lote
            processador.envio_sincrono = True
        return processador

    def _eletronic_document_send(self):
        simulados = self.filtered(
            lambda d: d.company_id.edoc_mock_mode and d.document_type in GENERICOS
        )
        for record in simulados:
            record._edoc_mock_authorize_generic()
        return super(Document, self - simulados)._eletronic_document_send()

    def _edoc_mock_authorize_generic(self):
        """CT-e e MDF-e: grava um protocolo simulado e autoriza o documento."""
        self.ensure_one()
        raiz_proc, raiz_prot, ns, motivo, campo_amb = GENERICOS[self.document_type]
        ambiente = self[campo_amb] if campo_amb in self._fields else "2"
        self._edoc_mock_check(ambiente or "2")
        # Ate a 16.0 de 10/2026 o envio rodava com o documento "a enviar";
        # com a maquina de estados (transitions) ele ja chega "enviada".
        if self.xml_error_message or self.state_edoc not in ("a_enviar", "enviada"):
            return
        evento = self.authorization_event_id
        enviado = evento.file_request_id.datas and base64.b64decode(
            evento.file_request_id.datas
        )
        proc_xml, numero = proc_generico(
            enviado,
            raiz_proc,
            raiz_prot,
            ns,
            self.document_key,
            self.company_id.state_id.ibge_code,
            motivo,
            ambiente or "2",
        )
        if evento:
            evento.set_done(
                status_code="100",
                response=motivo + SUFIXO,
                protocol_date=fields.Datetime.to_string(fields.Datetime.now()),
                protocol_number=numero,
                file_response_xml=proc_xml,
            )
        self.write({"status_code": "100", "status_name": motivo + SUFIXO})
        if hasattr(self, "_trigger_fsm"):
            self._trigger_fsm("action_authorize")
        else:
            self._change_state("autorizada")
