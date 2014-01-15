# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Danimar Ribeiro 22/08/2013                              #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
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
import time
import base64
import re
import string
from datetime import datetime
from os.path import expanduser

from openerp import pooler
from openerp.osv import orm
from openerp.tools.translate import _

def monta_caminho_nfe(ambiente, chave_nfe):
    try:            
        from pysped.nfe import ProcessadorNFe
    except ImportError as e:
        raise orm.except_orm(
            _(u'Erro!'), _(u"Biblioteca PySPED não instalada! " + str(e)))
    p = ProcessadorNFe()
    return p.monta_caminho_nfe(ambiente,chave_nfe)

def sign():
    pass

def cancel():
    pass
    
def send(cr, uid, ids, nfe_environment, context=None):
    try:            
        from pysped.nfe import ProcessadorNFe
        from pysped.nfe import webservices_flags
    except ImportError as e:
        raise orm.except_orm(
            _(u'Erro!'), _(u"Biblioteca PySPED não instalada! " + str(e)))
                         
    pool = pooler.get_pool(cr.dbname)
    invoice = pool.get('account.invoice').browse(cr, uid, ids[0], context)
    
    company_pool = pool.get('res.company')        
    company = company_pool.browse(cr, uid, invoice.company_id.id)
            
    p = ProcessadorNFe()
    p.versao = '2.00' if (company.nfe_version == '200') else '1.10'
    p.estado = company.partner_id.l10n_br_city_id.state_id.code
    
    file_content_decoded = base64.decodestring(company.nfe_a1_file)        
    p.certificado.stream_certificado = file_content_decoded
    p.certificado.senha = company.nfe_a1_password

    p.salva_arquivos      = True
    p.contingencia_SCAN   = False
    p.caminho = company.nfe_export_folder or os.path.join(expanduser("~"), company.name)
    
    nfe = self._serializer(cr, uid, ids, nfe_environment, context) #FIXME
    result = []
    
    for processo in p.processar_notas(nfe):   
        #result.append({'status':'success', 'message':'Recebido com sucesso.', 'key': nfe[0].infNFe.Id.valor, 'nfe': processo.envio.xml})
        #result.append({'status':'success', 'message':'Recebido com sucesso.','key': nfe[0].infNFe.Id.valor, 'nfe': processo.resposta.xml})
                                                    
        status = processo.resposta.cStat.valor
        message = processo.resposta.xMotivo.valor
        name = 'xml_enviado.xml'
        name_result = 'xml_retorno.xml'
        file_sent = processo.envio.xml
        file_result = processo.resposta.xml
        
        type_xml = ''
        if processo.webservice == webservices_flags.WS_NFE_CONSULTA:
            type_xml = 'Situação NF-e'
        elif processo.webservice == webservices_flags.WS_NFE_SITUACAO:                
            type_xml = 'Status'
        elif processo.webservice == webservices_flags.WS_NFE_ENVIO_LOTE:
            type_xml = 'Envio NF-e'
        elif processo.webservice == webservices_flags.WS_NFE_CONSULTA_RECIBO:
            type_xml = 'Recibo NF-e'                        
            
        if processo.resposta.status == 200:

            resultado = {'name':name,'name_result':name_result, 'message':message, 'xml_type':type_xml, 
                'status_code':status,'xml_sent': file_sent.encode('utf8'),'xml_result': file_result.encode('utf8'), 'status':'success'}

            if processo.webservice == webservices_flags.WS_NFE_CONSULTA_RECIBO:                
                resultado["status"] = "error"
                for prot in processo.resposta.protNFe:
                    resultado["status_code"] = prot.infProt.cStat.valor
                    resultado["message"] = prot.infProt.xMotivo.valor
                    resultado["nfe_key"] = prot.infProt.chNFe.valor
                    if prot.infProt.cStat.valor in ('100', '150', '110', '301', '302'):
                        nfe_xml = processo.resposta.dic_procNFe[prot.infProt.chNFe.valor].xml
                        danfe_pdf = processo.resposta.dic_procNFe[prot.infProt.chNFe.valor].danfe_pdf

                        danfe_nfe = {'name':'danfe.pdf','name_result':'nfe_protocolada.xml', 
                            'message':prot.infProt.xMotivo.valor, 'xml_type':'Danfe/NF-e', 
                            'status_code':prot.infProt.cStat.valor,'xml_sent': danfe_pdf,
                            'xml_result': nfe_xml.encode('utf8') , 'status':'success'}

                        resultado["status"] = "success"
                        result.append(danfe_nfe)

        else:
            resultado = {'name':name,'name_result':name_result, 'message':processo.resposta.original, 'xml_type':type_xml, 
                'status_code':processo.resposta.status,'xml_sent': file_sent.encode('utf8'),'xml_result': file_result.encode('utf8'), 'status':'error'}

        result.append(resultado)

    return result

#inutilização de numeração
def send_request_to_sefaz(self, cr, uid, ids, *args):    
    record = self.browse(cr, uid, ids[0])
    company_pool = self.pool.get('res.company')        
    company = company_pool.browse(cr, uid, record.company_id.id)
    
    validate_nfe_configuration(company)
    validate_nfe_invalidate_number(company, record)
    
    p = pysped.nfe.ProcessadorNFe()        
    p.versao = '2.00' if (company.nfe_version == '200') else '1.10'
    p.estado = company.partner_id.l10n_br_city_id.state_id.code

    file_content_decoded = base64.decodestring(company.nfe_a1_file)        
    p.certificado.stream_certificado = file_content_decoded
    p.certificado.senha = company.nfe_a1_password

    p.salva_arquivos      = True
    p.contingencia_SCAN   = False
    p.caminho = company.nfe_export_folder or os.path.join(expanduser("~"), company.name)            
            
    cnpj_partner = re.sub('[^0-9]','', company.partner_id.cnpj_cpf)
    serie = record.document_serie_id.code

    processo = p.inutilizar_nota(
        cnpj=cnpj_partner,
        serie=serie,
        numero_inicial=record.number_start,
        numero_final=record.number_end,
        justificativa=record.justificative)
               
    return processo