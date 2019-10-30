# -*- coding: utf-8 -*-
# Copyright (C) 2013  Danimar Ribeiro 26/06/2013
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import os
import logging
import datetime
import base64
from pytz import UTC


from odoo.tools.translate import _
from odoo import models, fields, api
from odoo.exceptions import RedirectWarning
from odoo.addons.l10n_br_account_product.sped.nfe.validator.config_check \
    import validate_nfe_configuration, validate_invoice_cancel
from odoo.addons.edoc_base.constantes import (
    AUTORIZADO,
    AUTORIZADO_OU_DENEGADO,
    DENEGADO,
    LOTE_EM_PROCESSAMENTO,
    LOTE_RECEBIDO,
    LOTE_PROCESSADO,
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




class AccountInvoice(models.Model):
    """account_invoice overwritten methods"""
    _inherit = 'account.invoice'

    def _get_nfe_factory(self, edoc_version):
        return NfeFactory().get_nfe(edoc_version)

    @api.multi
    def _edoc_export(self):
        self.ensure_one()

        if not self.company_id.processador_edoc == PROCESSADOR:
            return super(AccountInvoice, self)._edoc_export()

        validate_nfe_configuration(self.company_id)
        nfe_obj = self._get_nfe_factory(self.edoc_version)
        nfe = nfe_obj.get_xml(self, int(self.company_id.nfe_environment))[0]

        erro = XMLValidator.validation(nfe['nfe'], nfe_obj)
        nfe_key = nfe['key'][3:]
        if erro:
            raise RedirectWarning(erro, _(u'Erro na validaço da NFe!'))

        self.edoc_access_key = nfe_key
        nfe_file = nfe['nfe'].encode('utf8')
        return nfe_file

    @api.multi
    def _edoc_send(self):
        if not self.company_id.processador_edoc == PROCESSADOR:
            return super(AccountInvoice, self)._edoc_send()

        for inv in self:
            processador = self._get_nfe_factory(inv.edoc_version)

            #
            # Evento de autorização em rascunho
            #
            arquivo = inv.autorizacao_event_id.file_sent
            nfe = processador.set_xml(arquivo)

            #
            # Envia a nota
            #
            processo = None
            for p in send(inv.company_id, [nfe]):
                processo = p

            #
            # Se o último processo foi a consulta do status do serviço,
            # significa que ele não está online...
            #
            if processo.webservice == WS_NFE_SITUACAO:
                inv.state_edoc = SITUACAO_EDOC_EM_DIGITACAO
            #
            # Se o último processo foi a consulta da nota, significa que ela
            # já está emitida
            #
            elif processo.webservice == WS_NFE_CONSULTA:

                if processo.resposta.cStat.valor in AUTORIZADO:
                    inv._change_state(SITUACAO_EDOC_AUTORIZADA)
                elif processo.resposta.cStat.valor in DENEGADO:
                    inv._change_state(SITUACAO_FISCAL_DENEGADO)
                else:
                    inv._change_state(SITUACAO_EDOC_EM_DIGITACAO)
            #
            # Se o último processo foi o envio do lote, significa que a
            # consulta falhou, mas o envio não
            #
            elif processo.webservice == WS_NFE_ENVIO_LOTE:
                #
                # Lote recebido, vamos guardar o recibo
                #
                if processo.resposta.cStat.valor in LOTE_RECEBIDO:
                    inv.recibo = processo.resposta.infRec.nRec.valor
                else:
                    inv.edoc_status_code = processo.resposta.cStat.valor
                    inv.edoc_status_message = processo.resposta.xMotivo.valor
                    inv._change_state(SITUACAO_EDOC_REJEITADA)
            #
            # Se o último processo foi o retorno do recibo, a nota foi
            # rejeitada, denegada, autorizada, ou ainda não tem resposta
            #
            elif processo.webservice == WS_NFE_CONSULTA_RECIBO:
                #
                # Consulta ainda sem resposta, a nota ainda não foi processada
                #
                if processo.resposta.cStat.valor in LOTE_EM_PROCESSAMENTO:
                    inv._change_state(SITUACAO_EDOC_ENVIADA)
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

                        inv.autorizacao_event_id._grava_anexo(
                            procNFe.NFe.xml, 'xml'
                        )
                        inv.autorizacao_event_id.set_done(
                            procNFe.xml
                        )
                        # if inv.fiscal_document_id.code == '55':
                        #     inv.grava_pdf(nfe, procNFe.danfe_pdf)
                        # elif self.modelo == '65':
                        #     inv.grava_pdf(nfe, procNFe.danfce_pdf)
                        inv.edoc_protocol_number = protNFe.infProt.nProt.valor
                        inv.edoc_access_key = protNFe.infProt.chNFe.valor

                        if protNFe.infProt.cStat.valor in AUTORIZADO:
                            inv._change_state(SITUACAO_EDOC_AUTORIZADA)

                        else:
                            inv._change_state(SITUACAO_FISCAL_DENEGADO)

                        inv.edoc_status_code = protNFe.infProt.cStat.valor
                        inv.edoc_status_message = protNFe.infProt.xMotivo.valor

                    else:
                        inv.edoc_status_code = processo.resposta.cStat.valor
                        inv.edoc_status_message =\
                            processo.resposta.xMotivo.valor
                        inv._change_state(SITUACAO_EDOC_REJEITADA)
                else:
                    #
                    # Rejeitada por outros motivos, falha no schema etc. etc.
                    #
                    inv.edoc_status_code = processo.resposta.cStat.valor
                    inv.edoc_status_message = processo.resposta.xMotivo.valor
                    inv._change_state(SITUACAO_EDOC_REJEITADA)
        return True

    @api.multi
    def button_cancel(self):

        document_serie_id = self.document_serie_id
        fiscal_document_id = self.document_serie_id.fiscal_document_id
        electronic = self.document_serie_id.fiscal_document_id.electronic
        edoc_protocol = self.edoc_protocol_number
        emitente = self.issuer

        if ((document_serie_id and fiscal_document_id and not electronic) or
                not edoc_protocol) or emitente == u'1':
            return self.action_cancel()
        else:
            result = self.env['ir.actions.act_window'].for_xml_id(
                'nfe',
                'action_nfe_invoice_cancel_form')
            return result

    @api.multi
    def cancel_invoice_online(self, justificative):
        event_obj = self.env['l10n_br_account.document_event']

        for inv in self:
            if inv.state in ('open', 'paid'):

                validate_nfe_configuration(self.company_id)
                validate_invoice_cancel(inv)

                results = []
                try:
                    processo = cancel(
                        self.company_id,
                        inv.edoc_access_key,
                        inv.edoc_protocol_number,
                        justificative)
                    vals = {
                        'type': str(processo.webservice),
                        'status': processo.resposta.cStat.valor,
                        'response': '',
                        'company_id': self.company_id.id,
                        'origin': '[NF-E] {0}'.format(inv.fiscal_number),
                        'message': processo.resposta.xMotivo.valor,
                        'state': 'done',
                        'document_event_ids': inv.id}

                    self.attach_file_event(None, 'can', 'xml')

                    for prot in processo.resposta.retEvento:
                        vals["status"] = prot.infEvento.cStat.valor
                        vals["message"] = prot.infEvento.xEvento.valor
                        if vals["status"] in (
                                '101',  # Cancelamento de NF-e
                                # homologado
                                '128',
                                # Loto do evento processado
                                '135',  # Evento registrado e
                                # vinculado a NFC-e
                                '151',  # Cancelamento de NF-e
                                # homologado fora de prazo
                                '155'):  # Cancelamento homologado fora prazo
                            # Fixme:
                            result = super(AccountInvoice, self)\
                                .action_cancel()
                            if result:
                                self.write({'state': 'sefaz_cancelled',
                                            'edoc_status': vals["status"] +
                                            ' - ' + vals["message"]
                                            })
                                obj_cancel = self.env[
                                    'l10n_br_account.invoice.cancel']
                                obj = obj_cancel.create({
                                    'invoice_id': inv.id,
                                    'justificative': justificative,
                                })
                                vals['cancel_document_event_id'] = obj.id
                    results.append(vals)
                except Exception as e:
                    _logger.error(e.message, exc_info=True)
                    vals = {
                        'type': '-1',
                        'status': '000',
                        'response': 'response',
                        'company_id': self.company_id.id,
                        'origin': '[NF-E] {0}'.format(inv.fiscal_number),
                        'file_sent': 'OpenFalse',
                        'file_returned': 'False',
                        'message': 'Erro desconhecido ' + e.message,
                        'state': 'done',
                        'document_event_ids': inv.id
                    }
                    results.append(vals)
                finally:
                    for result in results:
                        event_obj.create(result)

            elif inv.state in ('sefaz_export', 'sefaz_exception'):
                _logger.error(
                    _(u'Invoice in invalid state to cancel online'),
                    exc_info=True)
                # TODO
        return

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
    def action_check_nfe(self):
        for inv in self:
            event_obj = self.env['l10n_br_account.document_event']
            # event = max(
            #     event_obj.search([('document_event_ids', '=', inv.id),
            #                       ('type', '=', '0')]))
            # arquivo = event.file_sent
            nfe_obj = self._get_nfe_factory(inv.edoc_version)

            nfe = []
            results = []
            protNFe = {}
            protNFe["state"] = 'sefaz_exception'
            protNFe["status_code"] = ''
            protNFe["message"] = ''
            protNFe["edoc_protocol_number"] = ''
            try:
                file_xml = monta_caminho_nfe(
                    inv.company_id, inv.edoc_access_key)
                # if inv.state not in (
                # 'open', 'paid', 'sefaz_cancelled'):
                #     file_xml = os.path.join(file_xml, 'tmp/')
                arquivo = os.path.join(
                    file_xml, inv.edoc_access_key + '-nfe.xml')
                nfe = nfe_obj.set_xml(arquivo)
                nfe.monta_chave()
                processo = check_key_nfe(inv.company_id, nfe.chave, nfe)
                vals = {
                    'type': str(processo.webservice),
                    'status': processo.resposta.cStat.valor,
                    'response': '',
                    'company_id': inv.company_id.id,
                    'origin': '[NF-E]' + inv.fiscal_number,
                    # TODO: Manipular os arquivos manualmente
                    # 'file_sent': processo.arquivos[0]['arquivo'],
                    # 'file_returned': processo.arquivos[1]['arquivo'],
                    'message': processo.resposta.xMotivo.valor,
                    'state': 'done',
                    'document_event_ids': inv.id}
                results.append(vals)
                if processo.webservice == 4:
                    prot = processo.resposta.protNFe
                    protNFe["status_code"] = prot.infProt.cStat.valor
                    protNFe["edoc_protocol_number"] = \
                        prot.infProt.nProt.valor
                    protNFe["message"] = prot.infProt.xMotivo.valor
                    vals["status"] = prot.infProt.cStat.valor
                    vals["message"] = prot.infProt.xMotivo.valor
                    if prot.infProt.cStat.valor in AUTORIZADO:
                        protNFe["state"] = 'open'
                        inv.invoice_validate()
                    elif prot.infProt.cStat.valor in DENEGADO:
                        protNFe["state"] = 'sefaz_denied'
                    self.attach_file_event(None, 'nfe', 'xml')
                    self.attach_file_event(None, None, 'pdf')
            except Exception as e:
                _logger.error(e.message, exc_info=True)
                vals = {
                    'type': '-1',
                    'status': '000',
                    'response': 'response',
                    'company_id': self.company_id.id,
                    'origin': '[NF-E]' + inv.fiscal_number,
                    'file_sent': 'False',
                    'file_returned': 'False',
                    'message': 'Erro desconhecido ' + str(e),
                    'state': 'done',
                    'document_event_ids': inv.id
                }
                results.append(vals)
            finally:
                for result in results:
                    if result['type'] == '0':
                        event_obj.write(result)
                    else:
                        event_obj.create(result)

                self.write({
                    'edoc_status': protNFe["status_code"] + ' - ' +
                    protNFe["message"],
                    'edoc_date': datetime.datetime.now(),
                    'state': protNFe["state"],
                    'edoc_protocol_number': protNFe["edoc_protocol_number"],
                })
        return True
