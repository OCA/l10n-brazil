# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Danimar Ribeiro 26/06/2013                              #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

import os
import pysped
import logging
import datetime
from openerp.osv import orm
from StringIO import StringIO
from openerp.tools.translate import _
from .sped.nfe.nfe_factory import NfeFactory
from .sped.nfe.validator.xml import XMLValidator
from openerp.addons.nfe.sped.nfe.processing.xml import send, cancel
from openerp.addons.nfe.sped.nfe.processing.xml import monta_caminho_nfe
from openerp.addons.nfe.sped.nfe.validator.config_check import validate_nfe_configuration, validate_invoice_cancel

_logger = logging.getLogger(__name__)

class AccountInvoice(orm.Model):
    """account_invoice overwritten methods"""
    _inherit = 'account.invoice'

    def attach_file_event(self, cr, uid, ids, seq, att_type, ext, context):
        """
        Implemente esse metodo na sua classe de manipulação de arquivos
        :param cr:
        :param uid:
        :param ids:
        :param seq:
        :param att_type:
        :param ext:
        :param context:
        :return:
        """
        return False

    def _get_nfe_factory(self, nfe_version):
        return NfeFactory().get_nfe(nfe_version)

    def nfe_export(self, cr, uid, ids, context=None):
        user_pool = self.pool.get('res.users')        
        if not context:
            context = user_pool.context_get(cr, uid, context)
            
        for inv in self.browse(cr, uid, ids, context):

            company_pool = self.pool.get('res.company')
            company = company_pool.browse(cr, uid, inv.company_id.id)

            validate_nfe_configuration(company)

            nfe_obj = self._get_nfe_factory(inv.nfe_version)

            # nfe_obj = NFe310()
            nfes = nfe_obj.get_xml(cr, uid, ids, int(company.nfe_environment), context)

            for nfe in nfes:
                # erro = nfe_obj.validation(nfe['nfe'])
                erro = XMLValidator.validation(nfe['nfe'], nfe_obj)
                nfe_key = nfe['key'][3:]
                if erro:
                    raise orm.except_orm(
                         _(u'Erro na validação da NFe!'), erro)

                self.write(cr, uid, inv.id, {'nfe_access_key': nfe_key})
                save_dir = os.path.join(monta_caminho_nfe(company, chave_nfe=nfe_key) + 'tmp/')
                nfe_file = nfe['nfe'].encode('utf8')

                file_path = save_dir + nfe_key + '-nfe.xml'
                try:
                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)
                    f = open(file_path, 'w')
                except IOError:
                    raise orm.except_orm(
                        _(u'Erro!'),
                        _(u"""Não foi possível salvar o arquivo em disco,
                            verifique as permissões de escrita e o caminho
                            da pasta"""))
                else:
                    f.write(nfe_file)
                    f.close()

                    event_obj = self.pool.get('l10n_br_account.document_event')
                    nfe_send_id = event_obj.create(cr, uid, {
                        'type': '0',
                        'company_id': company.id,
                        'origin': '[NF-E]' + inv.internal_number,
                        'file_sent': file_path,
                        'create_date': datetime.datetime.now(),
                        'state': 'draft',
                        'document_event_ids': inv.id
                        }, context)
                    self.write(cr, uid, ids, {'state':'sefaz_export'}, context=context)

    def action_invoice_send_nfe(self, cr, uid, ids, context=None):

        for inv in self.browse(cr, uid, ids):

            company_pool = self.pool.get('res.company')
            company = company_pool.browse(cr, uid, inv.company_id.id)
            event_obj = self.pool.get('l10n_br_account.document_event')
            event  = max(event_obj.search(cr, uid, [('document_event_ids','=',inv.id),('type','=','0')], context=context))
            send_event  = event_obj.browse(cr, uid, [event])[0]
            arquivo = send_event.file_sent
            nfe_obj = self._get_nfe_factory(inv.nfe_version)

            nfe = []
            results = []
            protNFe = {}
            protNFe["state"] = 'sefaz_exception'
            protNFe["status_code"] = ''
            protNFe["message"] = ''
            protNFe["nfe_protocol_number"] = ''
            try:
                nfe.append(nfe_obj.set_xml(arquivo))
                for processo in send(company, nfe):
                    vals = {
                            'type': str(processo.webservice),
                            'status': processo.resposta.cStat.valor,
                            'response': '',
                            'company_id': company.id,
                            'origin': '[NF-E]' + inv.internal_number,
                            #TODO: Manipular os arquivos manualmente
                            # 'file_sent': processo.arquivos[0]['arquivo'],
                            # 'file_returned': processo.arquivos[1]['arquivo'],
                            'message': processo.resposta.xMotivo.valor,
                            'state': 'done',
                            'document_event_ids': inv.id}
                    results.append(vals)
                    if processo.webservice == 1:                         
                        for prot in processo.resposta.protNFe:
                            protNFe["status_code"] = prot.infProt.cStat.valor
                            protNFe["nfe_protocol_number"] = prot.infProt.nProt.valor
                            protNFe["message"] = prot.infProt.xMotivo.valor
                            vals["status"] = prot.infProt.cStat.valor
                            vals["message"] = prot.infProt.xMotivo.valor
                            if prot.infProt.cStat.valor in ('100', '150', '110', '301', '302'):
                                protNFe["state"] = 'open'
                        self.attach_file_event(cr, uid, [inv.id], None, 'nfe', 'xml', context)
                        self.attach_file_event(cr, uid, [inv.id], None, None, 'pdf', context)
            except Exception as e:
                _logger.error(e.message,exc_info=True)
                vals = {
                        'type': '-1',
                        'status': '000',
                        'response': 'response',
                        'company_id': company.id,
                        'origin': '[NF-E]' + inv.internal_number,
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
                        event_obj.write(
                            cr, uid, inv.account_document_event_ids[0].id,
                            result, context)
                    else:
                        event_obj.create(cr, uid, result, context)

                self.write(cr, uid, inv.id, {
                     'nfe_status': protNFe["status_code"] + ' - ' + protNFe["message"],
                     'nfe_date': datetime.datetime.now(),
                     'state': protNFe["state"],
                     'nfe_protocol_number': protNFe["nfe_protocol_number"],
                     }, context)
        return True 
        
    def cancel_invoice_online(self, cr, uid, ids, justificative, context=None):
        
        for inv in self.browse(cr, uid, ids, context):

            document_serie_id = inv.document_serie_id
            fiscal_document_id = inv.document_serie_id.fiscal_document_id
            electronic = inv.document_serie_id.fiscal_document_id.electronic

            if (document_serie_id and fiscal_document_id and not electronic):
                return False
                      
            event_obj = self.pool.get('l10n_br_account.document_event')
            if inv.state in ('open','paid'):
                company_pool = self.pool.get('res.company')
                company = company_pool.browse(cr, uid, inv.company_id.id)
                
                validate_nfe_configuration(company)
                validate_invoice_cancel(inv)
            
                results = []   
                try:
                    processo = cancel(company, inv.nfe_access_key, inv.nfe_protocol_number, justificative) 
                    vals = {
                                'type': str(processo.webservice),
                                'status': processo.resposta.cStat.valor,
                                'response': '',
                                'company_id': company.id,
                                'origin': '[NF-E] {0}'.format(inv.internal_number),
                                # 'file_sent': processo.arquivos[0]['arquivo'] if len(processo.arquivos) > 0 else '',
                                # 'file_returned': processo.arquivos[1]['arquivo'] if len(processo.arquivos) > 0 else '',
                                'message': processo.resposta.xMotivo.valor,
                                'state': 'done',
                                'document_event_ids': inv.id}

                    self.attach_file_event(cr, uid, [inv.id], None, 'can', 'xml', context)
                    for prot in processo.resposta.retEvento:                        
                        vals["status"] = prot.infEvento.cStat.valor
                        vals["message"] = prot.infEvento.xEvento.valor
                        if vals["status"] == '135':
                            result = super(AccountInvoice, self).action_cancel(cr, uid, [inv.id], context)
                            if result:
                                self.write(cr, uid, [inv.id], {'state':'sefaz_cancelled',
                                                               'nfe_status': vals["status"]+ ' - ' +vals["message"]
                                                               })
                                obj_cancel = self.pool.get('l10n_br_account.invoice.cancel')
                                obj_cancel.create(cr,uid, 
                                   {'invoice_id': inv.id,
                                    'justificative': justificative,
                                    })                                                   
                    results.append(vals)
                except Exception as e:
                    _logger.error(e.message,exc_info=True)
                    vals = {
                            'type': '-1',
                            'status': '000',
                            'response': 'response',
                            'company_id': company.id,
                            'origin': '[NF-E] {0}'.format(inv.internal_number),
                            'file_sent': 'OpenFalse',
                            'file_returned': 'False',
                            'message': 'Erro desconhecido ' + e.message,
                            'state': 'done',
                            'document_event_ids': inv.id
                            }
                    results.append(vals)
                finally:
                    for result in results:
                        event_obj.create(cr, uid, result)    
             
            elif inv.state in ('sefaz_export','sefaz_exception'):
                _logger.error(_(u'Invoice in invalid state to cancel online'),exc_info=True)
                #TODO
        return

    # def str_pdf_Danfes(self, cr, uid, ids, context=None):
    #
    #     str_pdf = ""
    #     paths = []
    #
    #     for inv in self.browse(cr, uid, ids):
    #         company = inv.company_id
    #         nfe_key = inv.nfe_access_key
    #         nfe_obj = self._get_nfe_factory(inv.nfe_version)
    #
    #         procnfe = pysped.nfe.manual_401.ProcNFe_200()
    #
    #         try:
    #             if inv.state in ['open', 'paid', 'sefaz_cancelled']:
    #                 file_xml = os.path.join(monta_caminho_nfe(
    #                     company, chave_nfe=nfe_key))
    #
    #             else:
    #                 file_xml = os.path.join(os.path.join(
    #                     monta_caminho_nfe(company, chave_nfe=nfe_key), 'tmp/'))
    #
    #             procnfe.xml = os.path.join(file_xml, nfe_key + '-nfe.xml')
    #         except:
    #             raise orm.except_orm(('Error !'),
    #                                  ('Não é possível gerar a Danfe '
    #                                   '- Confirme o Documento'))
    #
    #         danfe = pysped.nfe.processador_nfe.DANFE()
    #         danfe.NFe = procnfe.NFe
    #         danfe.protNFe = procnfe.protNFe
    #         danfe.caminho = "/tmp/"
    #         danfe.gerar_danfe()
    #         paths.append(danfe.caminho + danfe.NFe.chave + '.pdf')
    #
    #     output = PdfFileWriter()
    #     s = StringIO()
    #
    #     # merge dos pdf criados
    #     for path in paths:
    #         pdf = PdfFileReader(file(path, "rb"))
    #
    #         for i in range(pdf.getNumPages()):
    #             output.addPage(pdf.getPage(i))
    #
    #         output.write(s)
    #
    #     str_pdf = s.getvalue()
    #     s.close()
    #
    #     return str_pdf

    def invoice_print(self, cr, uid, ids, context=None):

        for inv in self.browse(cr, uid, ids, context):

            document_serie_id = inv.document_serie_id
            fiscal_document_id = inv.document_serie_id.fiscal_document_id
            electronic = inv.document_serie_id.fiscal_document_id.electronic

            if (document_serie_id and fiscal_document_id and not electronic):
                return super(AccountInvoice, self).invoice_print(
                    cr, uid, ids, context=context)

            assert len(ids) == 1, 'This option should only be ' \
                                  'used for a single id at a time.'

            self.write(cr, uid, ids, {'sent': True}, context=context)
            datas = {
                'ids': ids,
                'model': 'account.invoice',
                'form': self.read(cr, uid, ids[0], context=context)
            }

            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'danfe_account_invoice',
                'datas': datas,
                'nodestroy': True
            }
