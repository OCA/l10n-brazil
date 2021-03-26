# Copyright (C) 2020  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

from odoo import api, models, fields
from odoo.exceptions import UserError
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_FISCAL_CANCELADO,
    CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
)


class DocumentCancel(models.Model):
    _inherit = 'l10n_br_fiscal.document.cancel'

    @api.multi
    def cancel_document(self, event_id):
        for record in self:
            if not record.document_id or not record.justificative:
                return super().cancel_document(event_id)

            processador = record.document_id._processador()

            evento = processador.cancela_documento(
                chave=record.document_id.key[3:],
                protocolo_autorizacao=record.document_id.protocolo_autorizacao,
                justificativa=record.justificative
            )
            processo = processador.enviar_lote_evento(
                lista_eventos=[evento]
            )
            event_id._grava_anexo(
                processo.envio_xml.decode('utf-8'), "xml"
            )

            for retevento in processo.resposta.retEvento:
                if not retevento.infEvento.chNFe == record.document_id.key[3:]:
                    continue

                if retevento.infEvento.cStat not in CANCELADO:
                    mensagem = 'Erro no cancelamento'
                    mensagem += '\nCódigo: ' + retevento.infEvento.cStat
                    mensagem += '\nMotivo: ' + retevento.infEvento.xMotivo
                    raise UserError(mensagem)
                else:
                    if retevento.infEvento.cStat == '155':
                        record.document_id.state_fiscal = \
                            SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO
                        record.document_id.state_edoc = SITUACAO_EDOC_CANCELADA
                    elif retevento.infEvento.cStat == '135':
                        record.document_id.state_fiscal = \
                            SITUACAO_FISCAL_CANCELADO
                        record.document_id.state_edoc = SITUACAO_EDOC_CANCELADA

                    record.document_id.document_cancel_id = record
                    record.document_id.cancel_event_id = event_id
                    record.document_id.data_hora_cancelamento = fields.Datetime.to_string(
                        datetime.fromisoformat(retevento.infEvento.dhRegEvento)
                    )
                    record.document_id.protocolo_cancelamento = retevento.infEvento.nProt

                event_id.set_done(
                    processo.retorno.content.decode('utf-8'),
                    status=retevento.infEvento.cStat,
                    message=retevento.infEvento.xMotivo
                )
