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
import re
import pysped.nfe
import base64
import datetime
import netsvc
from openerp.osv import osv, fields, orm
from openerp.tools.translate import _
from send_nfe import SendNFe
from os.path import expanduser
from sped.nfe.config_check import *


class account_invoice(osv.Model):
    #--- account_invoice overwritten methods
    _inherit = 'account.invoice'

    _columns = {
        'send_nfe_invoice_id': fields.many2one('l10n_br_nfe.send_sefaz', 'Envio NFe'),
        'cancel_nfe_invoice_id': fields.many2one('l10n_br_nfe.send_sefaz', 'Cancelamento NFe'),
    }

#     #Override methods of super class
#     def copy(self, cr, uid, ids, defaults, context=None):
#         defaults['send_nfe_invoice_id'] = None
#         return super(account_invoice,self).copy(cr, uid, ids, defaults, context)
#      def action_cancel(self, cr, uid, ids, context=None):
#          self.cancel_invoice_online(cr, uid, ids, context)
#          return super(account_invoice,self).action_cancel(cr, uid, ids, context)

    #---Workflow actions  

    def action_invoice_send_nfe(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids[0])
        company_pool = self.pool.get('res.company')
        company = company_pool.browse(cr, uid, record.company_id.id)

        validate_nfe_configuration(company)

        nfe_send_pool = self.pool.get('l10n_br_nfe.send_sefaz')
        nfe_send_id = nfe_send_pool.create(cr, uid, { 'name': 'Envio NFe', 'start_date': datetime.datetime.now()}, context)

        self.write(cr, uid, ids, {'send_nfe_invoice_id': nfe_send_id})

        erros = False   
        chave_nfe = ''
        status_sefaz = ''                     
        try:
            envio = SendNFe()
            resultados =  envio.send_nfe(cr, uid, ids, '2', context)

            nfe_send_pool.write(cr, uid, nfe_send_id,{ 'end_date': datetime.datetime.now(),'state':'done' }, context)
            result_pool =  self.pool.get('l10n_br_nfe.send_sefaz_result')
            for result in resultados:
                if result['status'] != 'success':
                    erros = True
                if result['xml_type'] == 'Recibo NF-e':
                    status_sefaz = result['status_code'] + ' - ' + result['message']
                    chave_nfe = result["nfe_key"] or ''

                result_pool.create(cr, uid, {'send_sefaz_id': nfe_send_id , 'xml_type': result['xml_type'], 
                            'name':result['name'], 'file':base64.b64encode(result['xml_sent']), 
                            'name_result':result['name_result'], 'file_result':base64.b64encode(result['xml_result']),
                            'status':result['status'], 'status_code':result['status_code'], 
                            'message':result['message']}, context)
        except Exception as e:
            status_sefaz = e.message
            erros = True

        data_envio = datetime.datetime.now()  
        if erros:            
            chave_nfe = ''   
            self.write(cr, uid, ids, {'state':'sefaz_exception'}, context)                                 
        else:            
            self.write(cr, uid, ids, {'state':'open'}, context)          

        self.write(cr, uid, ids, { 'nfe_access_key': chave_nfe, 'nfe_status':status_sefaz, 'nfe_date':data_envio }, context)        

#     #--- Class methods
#     def cancel_invoice_online(self, cr, uid, ids,context=None):        
#         record = self.browse(cr, uid, ids[0])
#         if record.document_serie_id:
#             if record.document_serie_id.fiscal_document_id:
#                 if not record.document_serie_id.fiscal_document_id.electronic:
#                     return
#                 
#         if record.state in ('open','paid'): 
#             company_pool = self.pool.get('res.company')        
#             company = company_pool.browse(cr, uid, record.company_id.id)
#             
#             validate_nfe_configuration(company)
#             validate_invoice_cancel(record)            
#                 
#             p = pysped.nfe.ProcessadorNFe()
#             
#             p.versao = '2.00' if (company.nfe_version == '200') else '1.10'
#             p.estado = company.partner_id.l10n_br_city_id.state_id.code
#         
#             file_content_decoded = base64.decodestring(company.nfe_a1_file)        
#             p.certificado.stream_certificado = file_content_decoded
#             p.certificado.senha = company.nfe_a1_password
#     
#             p.salva_arquivos      = True
#             p.contingencia_SCAN   = False
#             p.caminho = company.nfe_export_folder or os.path.join(expanduser("~"), company.name)
#             
#             processo = p.cancelar_nota_evento(
#                 chave_nfe = record.nfe_access_key,
#                 numero_protocolo=record.nfe_status,
#                 justificativa='Somente um teste de cancelamento' #TODO Colocar a justificativa de cancelamento num wizard de cancelamento.
#             )
# 
#             nfe_send_pool = self.pool.get('l10n_br_nfe.send_sefaz')
#             nfe_send_id = 0
#             if not record.send_nfe_invoice_id:
#                 nfe_send_id = nfe_send_pool.create(cr, uid, { 'name': 'Envio NFe', 'start_date': datetime.datetime.now()}, context)
#                 self.write(cr, uid, ids, {'send_nfe_invoice_id': nfe_send_id})
#             else:
#                 nfe_send_id = record.send_nfe_invoice_id.id
#                 
#                 
#             sucesso = 'Error'
#             if processo.resposta.infCanc.cStat.valor == '101':
#                 sucesso = 'success'
#             result_pool =  self.pool.get('l10n_br_nfe.send_sefaz_result')
#             result_pool.create(cr, uid, {'send_sefaz_id': nfe_send_id , 'xml_type': 'Cancelamento', 
#                             'name':'Envio_Cancelamento.xml', 'file':base64.b64encode(processo.envio.xml.encode('utf8')), 
#                             'name_result':'Retorno_Cancelamento.xml', 'file_result':base64.b64encode(processo.resposta.xml.encode('utf8')),
#                             'status':sucesso, 'status_code':processo.resposta.infCanc.cStat.valor, 
#                             'message':processo.resposta.infCanc.xMotivo.valor}, context)
#             
#         elif record.state in ('sefaz_export','sefaz_exception'):
#             result_pool =  self.pool.get('l10n_br_account.invoice.invalid.number')
#             
#             invalidate_number_id = result_pool.create(cr, uid, {'company_id':record.company_id.id,
#                 'fiscal_document_id':record.fiscal_document_id.id,'document_serie_id':record.document_serie_id.id,
#                 'number_start':record.internal_number,'number_end':record.internal_number, 
#                 'justificative':'Inutilização originada do cancelamento da fatura: ' + record.internal_number}, context)
#             
#             invoice_invalidate = result_pool.browse(cr, uid, invalidate_number_id, context)
#             invoice_invalidate.action_draft_done(cr, uid, [invalidate_number_id], context)
#             
#             