# -*- coding: utf-8 -*-
# Copyright (C) 2013  Danimar Ribeiro 26/06/2013
# Copyright (C) 2013  Luis Felipe Mileo
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import os
import logging
import datetime
import base64
from pytz import UTC


from odoo.tools.translate import _
from odoo import models, fields, api
from odoo.exceptions import RedirectWarning, UserError
from odoo.addons.l10n_br_account_product.sped.nfe.validator.config_check \
    import validate_nfe_configuration, validate_invoice_cancel
from odoo.addons.edoc_base.constantes import (
    AUTORIZADO,
    AUTORIZADO_OU_DENEGADO,
    DENEGADO,
    CANCELADO,
    LOTE_EM_PROCESSAMENTO,
    LOTE_RECEBIDO,
    LOTE_PROCESSADO,
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFCE,
    SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_INUTILIZADA,
    SITUACAO_FISCAL_REGULAR,
    SITUACAO_FISCAL_REGULAR_EXTEMPORANEO,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
    SITUACAO_FISCAL_DENEGADO,
    SITUACAO_FISCAL_INUTILIZADO,
    SITUACAO_FISCAL_COMPLEMENTAR,
    SITUACAO_FISCAL_COMPLEMENTAR_EXTEMPORANEO,
    SITUACAO_FISCAL_REGIME_ESPECIAL,
    SITUACAO_FISCAL_MERCADORIA_NAO_CIRCULOU,
    SITUACAO_FISCAL_MERCADORIA_NAO_RECEBIDA,
)

from ..sped.nfe.nfe_factory import NfeFactory
from ..sped.nfe.validator.xml import XMLValidator
from ..sped.nfe.processing.xml import send, cancel
from ..sped.nfe.processing.xml import monta_caminho_nfe
from ..sped.nfe.processing.xml import check_key_nfe
from ..sped.nfe.processing.xml import send_correction_letter


_logger = logging.getLogger(__name__)

try:
    from pysped.nfe.webservices_flags import (
        WS_NFE_SITUACAO,
        WS_NFE_CONSULTA,
        WS_NFE_ENVIO_LOTE,
        WS_NFE_CONSULTA_RECIBO,
    )
except (ImportError, IOError) as err:
    _logger.debug(err)

PROCESSADOR = 'pysped'


def fiter_processador_pysped(record):
    if (record.processador_edoc == PROCESSADOR and
            record.fiscal_document_id.code in [
                MODELO_FISCAL_NFE,
                MODELO_FISCAL_NFCE,
            ]):
        return True
    return False


class AccountInvoice(models.Model):
    """account_invoice overwritten methods"""
    _inherit = 'account.invoice'

    def _get_nfe_factory(self, edoc_version):
        return NfeFactory().get_nfe(edoc_version)

    @api.multi
    def _edoc_export(self):
        super(AccountInvoice, self)._edoc_export()
        for record in self.filtered(fiter_processador_pysped):

            validate_nfe_configuration(record.company_id)
            nfe_obj = record._get_nfe_factory(record.edoc_version)
            nfe = nfe_obj.get_xml(
                record, int(record.company_id.nfe_environment))[0]

            erro = XMLValidator.validation(nfe['nfe'], nfe_obj)
            nfe_key = nfe['key'][3:]
            if erro:
                raise RedirectWarning(erro, _(u'Erro na validaço da NFe!'))

            record.edoc_access_key = nfe_key
            nfe_file = nfe['nfe'].encode('utf8')

            event_id = self._gerar_evento(nfe_file, type="0")
            record.autorizacao_event_id = event_id
            record._change_state(SITUACAO_EDOC_A_ENVIAR)

    @api.multi
    def _edoc_send(self):
        super(AccountInvoice, self)._edoc_send()
        for record in self.filtered(fiter_processador_pysped):
            processador = self._get_nfe_factory(record.edoc_version)

            #
            # Evento de autorização em rascunho
            #
            arquivo = record.autorizacao_event_id.file_sent
            nfe = processador.set_xml(arquivo)

            #
            # Envia a nota
            #
            processo = None
            for p in send(record.company_id, [nfe]):
                processo = p

            #
            # Se o último processo foi a consulta do status do serviço,
            # significa que ele não está online...
            #
            if processo.webservice == WS_NFE_SITUACAO:
                record.state_edoc = SITUACAO_EDOC_EM_DIGITACAO
            #
            # Se o último processo foi a consulta da nota, significa que ela
            # já está emitida
            #
            elif processo.webservice == WS_NFE_CONSULTA:

                if processo.resposta.cStat.valor in AUTORIZADO:
                    record._change_state(SITUACAO_EDOC_AUTORIZADA)
                elif processo.resposta.cStat.valor in DENEGADO:
                    record._change_state(SITUACAO_FISCAL_DENEGADO)
                else:
                    record._change_state(SITUACAO_EDOC_EM_DIGITACAO)
            #
            # Se o último processo foi o envio do lote, significa que a
            # consulta falhou, mas o envio não
            #
            elif processo.webservice == WS_NFE_ENVIO_LOTE:
                #
                # Lote recebido, vamos guardar o recibo
                #
                if processo.resposta.cStat.valor in LOTE_RECEBIDO:
                    record.recibo = processo.resposta.infRec.nRec.valor
                else:
                    record.edoc_status_code = processo.resposta.cStat.valor
                    record.edoc_status_message = \
                        processo.resposta.xMotivo.valor
                    record._change_state(SITUACAO_EDOC_REJEITADA)
            #
            # Se o último processo foi o retorno do recibo, a nota foi
            # rejeitada, denegada, autorizada, ou ainda não tem resposta
            #
            elif processo.webservice == WS_NFE_CONSULTA_RECIBO:
                #
                # Consulta ainda sem resposta, a nota ainda não foi processada
                #
                if processo.resposta.cStat.valor in LOTE_EM_PROCESSAMENTO:
                    record._change_state(SITUACAO_EDOC_ENVIADA)
                #
                # Lote processado
                #
                elif processo.resposta.cStat.valor in LOTE_PROCESSADO:
                    protNFe = processo.resposta.protNFe[0]

                    #
                    # Autorizada ou denegada
                    #
                    if protNFe.infProt.cStat.valor in AUTORIZADO_OU_DENEGADO:
                        procNFe = processo.resposta.dic_procNFe[nfe.chave]

                        record.autorizacao_event_id._grava_anexo(
                            procNFe.NFe.xml, 'xml'
                        )
                        record.autorizacao_event_id.set_done(
                            procNFe.xml
                        )
                        # if record.fiscal_document_id.code == '55':
                        #     record.grava_pdf(nfe, procNFe.danfe_pdf)
                        # elif self.modelo == '65':
                        #     record.grava_pdf(nfe, procNFe.danfce_pdf)
                        record.edoc_protocol_number = \
                            protNFe.infProt.nProt.valor
                        record.edoc_access_key = protNFe.infProt.chNFe.valor

                        if protNFe.infProt.cStat.valor in AUTORIZADO:
                            record._change_state(SITUACAO_EDOC_AUTORIZADA)

                        else:
                            record._change_state(SITUACAO_FISCAL_DENEGADO)

                        record.edoc_status_code = protNFe.infProt.cStat.valor
                        record.edoc_status_message = \
                            protNFe.infProt.xMotivo.valor

                    else:
                        record.edoc_status_code = processo.resposta.cStat.valor
                        record.edoc_status_message =\
                            processo.resposta.xMotivo.valor
                        record._change_state(SITUACAO_EDOC_REJEITADA)
                else:
                    #
                    # Rejeitada por outros motivos, falha no schema etc. etc.
                    #
                    record.edoc_status_code = processo.resposta.cStat.valor
                    record.edoc_status_message = \
                        processo.resposta.xMotivo.valor
                    record._change_state(SITUACAO_EDOC_REJEITADA)

    @api.multi
    def cancel_invoice_online(self, justificative):
        event_obj = self.env['l10n_br_account.document_event']

        for inv in self:
            if inv.state in ('open', 'paid'):
                validate_nfe_configuration(self.company_id)
                validate_invoice_cancel(inv)

                processo = cancel(
                    inv.company_id,
                    inv.edoc_access_key,
                    inv.edoc_protocol_number,
                    justificative
                )

                if inv.edoc_access_key in processo.resposta.dic_procEvento:
                    procevento = processo.resposta.dic_procEvento[
                        inv.edoc_access_key
                    ]
                    retevento = procevento.retEvento

                    if retevento.infEvento.cStat.valor not in CANCELADO:
                        mensagem = 'Erro no cancelamento'
                        mensagem += '\nCódigo: ' + \
                                    retevento.infEvento.cStat.valor
                        mensagem += '\nMotivo: ' + \
                                    retevento.infEvento.xMotivo.valor
                        raise UserError(mensagem)


                data_cancelamento = retevento.infEvento.dhRegEvento.valor
                data_cancelamento = UTC.normalize(data_cancelamento)

                # self.data_hora_cancelamento = data_cancelamento
                # self.protocolo_cancelamento = \
                #     procevento.retEvento.infEvento.nProt.valor

                if procevento.retEvento.infEvento.cStat.valor == '155':
                    inv.state_fiscal = SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO
                    inv.state_edoc = SITUACAO_EDOC_CANCELADA
                elif procevento.retEvento.infEvento.cStat.valor == '135':
                    inv.state_fiscal = SITUACAO_FISCAL_CANCELADO
                    inv.state_edoc = SITUACAO_EDOC_CANCELADA

    @api.multi
    def invoice_print(self):

        for inv in self:

            document_serie_id = inv.document_serie_id
            fiscal_document_id = inv.document_serie_id.fiscal_document_id
            electronic = inv.document_serie_id.fiscal_document_id.electronic

            if document_serie_id and fiscal_document_id and not electronic:
                return super(AccountInvoice, self).invoice_print()

            assert len(inv.ids) == 1, 'This option should only be ' \
                                      'used for a single id at a time.'

            self.write({'sent': True})
            datas = {
                'ids': inv.ids,
                'model': 'account.invoice',
                'form': self.read()
            }

            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'danfe_account_invoice',
                'datas': datas,
                'nodestroy': True
            }

    @api.multi
    def action_edoc_check(self):
        for record in self:
            record._consultar_nfe()

    def _consultar_nfe(self, processador=None, nfe=None):
        #
        # Se a nota já foi emitida: autorizada, rejeitada e denegada
        # E não temos todos os dados, tentamos consultar a nota.
        #

        if not processador:
            processador = self._get_nfe_factory(self.edoc_version)

        if not nfe:
            file_xml = monta_caminho_nfe(
                self.company_id, self.edoc_access_key)
            arquivo = os.path.join(
                file_xml, self.edoc_access_key + '-nfe.xml')
            nfe = processador.set_xml(arquivo)
            nfe.monta_chave()

        consulta = check_key_nfe(self.company_id, nfe.chave, nfe)

        if nfe.procNFe:
            procNFe = nfe.procNFe


            data_autorizacao = \
                consulta.resposta.protNFe.infProt.dhRecbto.valor
            data_autorizacao = UTC.normalize(data_autorizacao)

            print data_autorizacao
            print consulta.resposta.protNFe.infProt.nProt.valor
            print consulta.resposta.protNFe.infProt.chNFe.valor

            if consulta.resposta.cStat.valor in AUTORIZADO:
                print "Autorizado"
            elif consulta.resposta.cStat.valor in DENEGADO:
                print "Denegado"
            elif consulta.resposta.cStat.valor in CANCELADO:
                print "Cancelado"

    def cce_invoice_online(self, mensagem):
        for invoice in self:
            chave_nfe = invoice.edoc_access_key
            event_obj = self.env['l10n_br_account.document_event']
            sequencia = len(invoice.cce_document_ids) + 1
            results = []
            try:
                processo = send_correction_letter(
                    invoice.company_id,
                    chave_nfe,
                    sequencia,
                    mensagem)
                vals = {
                    'type': str(processo.webservice),
                    'status': processo.resposta.retEvento[0].infEvento.
                        cStat.valor,
                    'response': '',
                    'company_id': invoice.company_id.id,
                    'origin': '[CC-E] ' + str(invoice.fiscal_number),
                    'message': processo.resposta.retEvento[0].infEvento.
                        xEvento.valor,
                    'state': 'done',
                    'document_event_ids': invoice.id}
                results.append(vals)
                # invoice.attach_file_event(
                #     sequencia,
                #     'cce',
                #     'xml')

            except Exception as e:
                vals = {
                    'type': '-1',
                    'status': '000',
                    'response': 'response',
                    'company_id': invoice.company_id.id,
                    'origin': '[CC-E]' + str(invoice.fiscal_number),
                    'file_sent': 'False',
                    'file_returned': 'False',
                    'message': 'Erro desconhecido ' + e.message,
                    'state': 'done',
                    'document_event_ids': invoice.id,
                }
                results.append(vals)
            finally:
                for result in results:
                    event_obj.create(result)
                    invoice.cce_document_ids.create({
                        'invoice_id': invoice.id,
                        'motivo': mensagem,
                        'sequencia': sequencia,
                    })
        return {'type': 'ir.actions.act_window_close'}
