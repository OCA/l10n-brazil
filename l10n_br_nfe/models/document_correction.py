# Copyright (C) 2020  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models
from odoo.exceptions import UserError


class DocumentCorrection(models.Model):
    _inherit = 'l10n_br_fiscal.document.correction'

    @api.multi
    def correction(self, event_id):
        for record in self:
            if not record.document_id or not record.justificative:
                return super().correction(event_id)

            processador = record.document_id._processador()

            evento = processador.carta_correcao(
                chave=record.document_id.key[3:],
                sequencia=record.sequencia,
                justificativa=record.justificative.replace('\n', '\\n')
            )
            processo = processador.enviar_lote_evento(
                lista_eventos=[evento]
            )

            for retevento in processo.resposta.retEvento:
                if not retevento.infEvento.chNFe == record.document_id.key[3:]:
                    continue

                if retevento.infEvento.cStat not in ('135', '136'):
                    mensagem = 'Erro na carta de correção'
                    mensagem += '\nCódigo: ' + retevento.infEvento.cStat
                    mensagem += '\nMotivo: ' + retevento.infEvento.xMotivo
                    raise UserError(mensagem)

                event_id.write({
                    'file_sent': processo.envio_xml,
                    'file_returned': processo.retorno.content,
                    'status': retevento.infEvento.cStat,
                    'message': retevento.infEvento.xMotivo,
                    'state': 'done',
                })
