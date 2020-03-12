# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.exceptions import UserError


class DocumentCorrection(models.Model):
    _name = "l10n_br_fiscal.document.correction"
    _inherit = "l10n_br_fiscal.event.abstract"
    _description = "Fiscal Document Correction Record"

    sequencia = fields.Char(
        string=u"Sequência", help=u"Indica a sequência da carta de correcão"
    )

    cce_document_event_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.event",
        inverse_name="correction_document_event_id",
        string=u"Eventos",
    )

    @api.multi
    def correction(self, event_id):
        for record in self:
            if not record.document_id or not record.justificative:
                continue

            processador = record.document_id._processador()

            evento = processador.carta_correcao(
                chave=record.document_id.key[3:],
                sequencia=record.sequencia,
                justificativa=record.justificative
            )
            processo = processador.enviar_lote_evento(
                lista_eventos=[evento]
            )

            for retevento in processo.resposta.retEvento:
                if not retevento.infEvento.chNFe == \
                       record.document_id.key[3:]:
                    continue

                if retevento.infEvento.cStat not in ('135', '136'):
                    mensagem = 'Erro na carta de correção'
                    mensagem += '\nCódigo: ' + retevento.infEvento.cStat
                    mensagem += '\nMotivo: ' + \
                                retevento.infEvento.xMotivo
                    raise UserError(mensagem)

                event_id.write({
                    'file_sent': processo.envio_xml,
                    'file_returned': processo.retorno.content,
                    'status': retevento.infEvento.cStat,
                    'message': retevento.infEvento.xMotivo,
                    'state': 'done',
                })
