# Copyright (C) 2020  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.l10n_br_fiscal.constants.fiscal import \
    SITUACAO_EDOC_INUTILIZADA
from erpbrasil.assinatura import certificado as cert
from erpbrasil.edoc import NFe as edoc_nfe
from erpbrasil.transmissao import TransmissaoSOAP
from requests import Session


class InvalidateNumber(models.Model):
    _inherit = 'l10n_br_fiscal.document.invalidate_number'

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
            transmissao, self.company_id.state_id.ibge_code,
            versao='4.00', ambiente='2'
        )

    @api.multi
    def invalidate(self, event_id):
        for record in self:
            processador = record._processador()

            evento = processador.inutilizacao(
                cnpj=record.company_id.cnpj_cpf,
                mod=record.document_serie_id.document_type_id.code,
                serie=record.document_serie_id.code,
                num_ini=record.number_start,
                num_fin=record.number_end,
                justificativa=record.justificative
            )

            processo = processador.envia_inutilizacao(
                evento=evento
            )

            event_id.write({
                'file_sent': processo.envio_xml,
                'file_returned': processo.retorno.content,
                'status': processo.resposta.infInut.cStat,
                'message': processo.resposta.infInut.xMotivo,
            })

            if processo.resposta.infInut.cStat == '102':
                super(InvalidateNumber, record).invalidate(event_id)

