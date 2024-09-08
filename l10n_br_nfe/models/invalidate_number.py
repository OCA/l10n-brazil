# Copyright (C) 2020  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

from erpbrasil.base.misc import punctuation_rm
from erpbrasil.transmissao import TransmissaoSOAP
from nfelib.nfe.ws.edoc_legacy import NFCeAdapter as edoc_nfce
from nfelib.nfe.ws.edoc_legacy import NFeAdapter as edoc_nfe
from requests import Session

from odoo import fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import EVENT_ENV_HML, EVENT_ENV_PROD


class InvalidateNumber(models.Model):
    _inherit = "l10n_br_fiscal.invalidate.number"

    def _processador(self):
        certificado = self.env.company._get_br_ecertificate()
        session = Session()
        session.verify = False
        params = {
            "transmissao": TransmissaoSOAP(certificado, session),
            "uf": self.company_id.state_id.ibge_code,
            "versao": "4.00",
            "ambiente": self.company_id.nfe_environment,
        }

        if self.document_type_id.code == "65":
            params.update(
                csc_token=self.company_id.nfce_csc_token,
                csc_code=self.company_id.nfce_csc_code,
            )
            return edoc_nfce(**params)

        return edoc_nfe(**params)

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

        if hasattr(processo.resposta.infInut, "dhRegEvento"):
            date_response = processo.resposta.infInut.dhRegEvento
        elif hasattr(processo.resposta.infInut, "dhRecbto"):
            date_response = processo.resposta.infInut.dhRecbto

        event_id.set_done(
            status_code=processo.resposta.infInut.cStat,
            response=processo.resposta.infInut.xMotivo,
            protocol_date=fields.Datetime.to_string(
                datetime.fromisoformat(date_response)
            ),
            protocol_number=processo.resposta.infInut.nProt,
            file_response_xml=processo.retorno.content.decode("utf-8"),
        )

        if processo.resposta.infInut.cStat == "102":
            return super()._invalidate(document_id)
