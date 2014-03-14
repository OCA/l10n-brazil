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

from pysped.nfe import ProcessadorNFe
from pysped.nfe import webservices_flags

def processo(company):
    
    p = ProcessadorNFe()
    p.ambiente = ambiente = int(company.nfe_environment)
    p.versao = '2.00' if (company.nfe_version == '200') else '1.10'
    p.estado = company.partner_id.l10n_br_city_id.state_id.code
    p.certificado.stream_certificado = base64.decodestring(company.nfe_a1_file)
    p.certificado.senha = company.nfe_a1_password
    p.salva_arquivos      = True
    p.contingencia_SCAN   = False
    p.caminho = company.nfe_export_folder or os.path.join(expanduser("~"), company.name)
    
    return p


def monta_caminho_nfe(ambiente, chave_nfe):
    
    p = ProcessadorNFe()
    return p.monta_caminho_nfe(ambiente,chave_nfe)

def check_key_nfe(company, chave_nfe, nfe=False):
    
    p = processo(company)
    return  p.consultar_nota(p.ambiente,chave_nfe,nfe)


def check_partner(company,cnpj_cpf, estado=None, ie=None):
    
    if not estado:
        estado = company.partner_id.state_id.code
    cnpj_cpf = (re.sub('[%s]' % re.escape(string.punctuation), '', cnpj_cpf or ''))
        
    p = processo(company)
    
    return  p.consultar_cadastro(estado, ie, cnpj_cpf)

def sign():
    pass

def cancel():
    pass
    
def send(company, nfe):
                        
    p = processo(company)
    return p.processar_notas(nfe)

        #result.append({'status':'success', 'message':'Recebido com sucesso.', 'key': nfe[0].infNFe.Id.valor, 'nfe': processo.envio.xml})
        #result.append({'status':'success', 'message':'Recebido com sucesso.','key': nfe[0].infNFe.Id.valor, 'nfe': processo.resposta.xml})


        # print dir(processo)
        # print "\n Arquivos" , processo.arquivos[0]['arquivo']
        # print "\n Arquivos" , processo.arquivos[1]['arquivo']

        # print "\n Envio" ,  dir(processo.envio)
        # print "\n Resposta" ,  dir(processo.resposta)
        # print "\n WebService" ,  dir(processo.webservice)


        # type_xml = ''

        # status = 
        # message = 
        # file_sent =
        # file_result =

                       
            
        # if processo.resposta.status == 200:

        #     resultado = {
        #         'name':name,
        #         'name_result':name_result,
        #         'message':message,
        #         'xml_type':type_xml,
        #         'status_code':status,
        #         'xml_sent': file_sent,
        #         'xml_result': file_result,
        #         'status':'success'
        #         }

        #     if processo.webservice == webservices_flags.WS_NFE_CONSULTA_RECIBO:                
        #         resultado["status"] = "error"
                
        #         for prot in processo.resposta.protNFe:
                    
        #             resultado["status_code"] = prot.infProt.cStat.valor
        #             resultado["message"] = prot.infProt.xMotivo.valor
        #             resultado["nfe_key"] = prot.infProt.chNFe.valor

        #             if prot.infProt.cStat.valor in ('100', '150', '110', '301', '302'):
        #                 nfe_xml = processo.resposta.dic_procNFe[prot.infProt.chNFe.valor].xml
        #                 #danfe_pdf = processo.resposta.dic_procNFe[prot.infProt.chNFe.valor].danfe_pdf
        #                 danfe_nfe = {
        #                     'name':'danfe.pdf',
        #                     'name_result':'nfe_protocolada.xml', 
        #                     'message':prot.infProt.xMotivo.valor, 
        #                     'xml_type':'Danfe/NF-e', 
        #                     'status_code':prot.infProt.cStat.valor,
        #                     'xml_sent': 'danfe_pdf',
        #                     'xml_result': nfe_xml.encode('utf8') , 
        #                     'status':'success'}

        #                 resultado["status"] = "success"
        #                 result.append(danfe_nfe)
        # else:
        #     resultado = {
        #         'name':name,
        #         'name_result':name_result, 
        #         'message':processo.resposta.original, 
        #         'xml_type':type_xml, 
        #         'status_code':processo.resposta.status,
        #         'xml_sent': file_sent,
        #         'xml_result': file_result, 
        #         'status':'error'
        #         }
        # result.append(resultado)
    # return result

#inutilização de numeração

def invalidate(company, invalidate_number):
                        
    p = processo(company)
    
    cnpj_partner = re.sub('[^0-9]','', company.partner_id.cnpj_cpf)
    serie = invalidate_number.document_serie_id.code

    processo = p.inutilizar_nota(
        cnpj=cnpj_partner,
        serie=serie,
        numero_inicial=invalidate_number.number_start,
        numero_final=invalidate_number.number_end,
        justificativa=invalidate_number.justificative)
               
    return processo
