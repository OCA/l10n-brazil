# Copyright (C) 2020  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from datetime import datetime

from erpbrasil.assinatura import certificado as cert
from erpbrasil.edoc.nfe import NFe as edoc_nfe
from erpbrasil.transmissao import TransmissaoSOAP
from requests import Session

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import EVENT_ENV_HML, EVENT_ENV_PROD

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base.misc import punctuation_rm
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class InvalidateNumber(models.Model):
    _inherit = "l10n_br_fiscal.invalidate.number"

    def _processador(self):
        if not self.company_id.certificate_nfe_id:
            raise UserError(_("Certificado não encontrado"))

        certificado = cert.Certificado(
            arquivo=self.company_id.certificate_nfe_id.file,
            senha=self.company_id.certificate_nfe_id.password,
        )
        session = Session()
        session.verify = False
        transmissao = TransmissaoSOAP(certificado, session)
        return edoc_nfe(
            transmissao,
            self.company_id.state_id.ibge_code,
            versao="4.00",
            ambiente=self.company_id.nfe_environment,
        )

    def _invalidate(self, document_id=False):
        processador = self._processador()
        evento = processador.inutilizacao(
            cnpj=punctuation_rm(self.company_id.cnpj_cpf),
            mod=self.document_type_id.code,
            serie=self.document_serie_id.code,
            num_ini=self.number_start,
            num_fin=self.number_end,
            justificativa=self.justification.replace("\n", "\\n"),
        )

        processo = processador.envia_inutilizacao(evento=evento)

        event_id = self.event_ids.create_event_save_xml(
            company_id=self.company_id,
            environment=(
                EVENT_ENV_PROD
                if self.company_id.nfe_environment == "1"
                else EVENT_ENV_HML
            ),
            event_type="3",
            xml_file=processo.envio_xml.decode("utf-8"),
            invalidate_number_id=self,
        )

        if document_id:
            event_id.document_id = document_id
        self.event_ids |= event_id
        self.authorization_event_id = event_id

        if hasattr(processo.resposta.inf_inut, "dh_reg_evento"):
            date_response = processo.resposta.inf_inut.dh_reg_evento
        elif hasattr(processo.resposta.inf_inut, "dh_recbto"):
            date_response = processo.resposta.inf_inut.dh_recbto

        event_id.set_done(
            status_code=processo.resposta.inf_inut.c_stat,
            response=processo.resposta.inf_inut.x_motivo,
            protocol_date=fields.Datetime.to_string(
                datetime.fromisoformat(date_response)
            ),
            protocol_number=processo.resposta.inf_inut.n_prot,
            file_response_xml=processo.retorno.content.decode("utf-8"),
        )

        if processo.resposta.inf_inut.c_stat == "102":
            return super(InvalidateNumber, self)._invalidate(document_id)
