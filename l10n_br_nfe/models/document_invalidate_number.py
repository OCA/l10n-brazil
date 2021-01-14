# Copyright (C) 2020  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from requests import Session

from erpbrasil.assinatura import certificado as cert
from erpbrasil.edoc.nfe import NFe as edoc_nfe
from erpbrasil.transmissao import TransmissaoSOAP

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_INUTILIZADA,
)


class DocumentInvalidateNumber(models.Model):
    _inherit = 'l10n_br_fiscal.document.invalidate.number'

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
                cnpj=record.company_id.cnpj_cpf.replace('.', '').replace(
                    '/', '').replace('-', ''),
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
                event_id.state = 'done'
                record.state = 'done'
                if record.document_id:
                    record.document_id.state_edoc = SITUACAO_EDOC_INUTILIZADA
                else:
                    for number in range(record.number_start,
                                        record.number_end + 1):
                        record.env['l10n_br_fiscal.document'].create({
                            'document_serie_id': record.document_serie_id.id,
                            'document_type_id':
                                record.document_serie_id.document_type_id.id,
                            'company_id': record.company_id.id,
                            'state_edoc': SITUACAO_EDOC_INUTILIZADA,
                            'issuer': 'company',
                            'number': str(number),
                        })
