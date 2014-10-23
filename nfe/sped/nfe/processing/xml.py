# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Danimar Ribeiro 22/08/2013                              #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
# Copyright (C) 2014  Luis Felipe Mileo - KMEE - www.kmee.com.br              #
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

from pysped.nfe.danfe import DANFE
from PIL import Image
from StringIO import StringIO

def __processo(company):
    
    p = ProcessadorNFe()
    p.ambiente = int(company.nfe_environment)
    p.versao = company.nfe_version
    p.estado = company.partner_id.l10n_br_city_id.state_id.code
    p.certificado.stream_certificado = base64.decodestring(company.nfe_a1_file)
    p.certificado.senha = company.nfe_a1_password
    p.salva_arquivos      = True
    p.contingencia_SCAN   = False
    p.caminho = company.nfe_export_folder
    return p

def monta_caminho_nfe(company, chave_nfe):
    p = __processo(company)
    return p.monta_caminho_nfe(p.ambiente,chave_nfe)

def check_key_nfe(company, chave_nfe, nfe=False):
    
    p = __processo(company)
    return  p.consultar_nota(p.ambiente,chave_nfe,nfe)

def check_partner(company,cnpj_cpf, estado=None, ie=None):
    
    p = __processo(company)    
    if not estado:
        estado = company.partner_id.state_id.code
    cnpj_cpf = (re.sub('[%s]' % re.escape(string.punctuation), '', cnpj_cpf or ''))
    return  p.consultar_cadastro(estado, ie, cnpj_cpf)

def sign():
    pass
    
def send(company, nfe):
                        
    p = __processo(company)
    logo = company.logo
    logo_image = Image.open(StringIO(logo.decode('base64')))
    logo_image.save(company.nfe_export_folder + "/company_logo.png")
    p.danfe.logo = company.nfe_export_folder + '/company_logo.png'
    p.danfe.nome_sistema = company.nfe_email or u"Odoo/OpenERP - Sistema de Gestao Empresarial de Codigo Aberto - 100%% WEB - www.openerpbrasil.org"
    
    
    return p.processar_notas(nfe)

def cancel(company, nfe_access_key, nfe_protocol_number, justificative):
    p = processo(company)
    
    p = __processo(company)
    return p.cancelar_nota_evento(
        chave_nfe = nfe_access_key,
        numero_protocolo=nfe_protocol_number,
        justificativa=justificative
    )
       
def invalidate(company, invalidate_number):
                        
    p = __processo(company)
    cnpj_partner = re.sub('[^0-9]','', company.partner_id.cnpj_cpf)
    serie = invalidate_number.document_serie_id.code
    return p.inutilizar_nota(
        cnpj=cnpj_partner,
        serie=serie,
        numero_inicial=invalidate_number.number_start,
        numero_final=invalidate_number.number_end,
        justificativa=invalidate_number.justificative)

def send_correction_letter(company, chave_nfe, numero_sequencia ,correcao):
    
    p = __processo(company)
    return p.corrigir_nota_evento( p.ambiente, chave_nfe, numero_sequencia, correcao)

