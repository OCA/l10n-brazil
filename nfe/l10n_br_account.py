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

class l10n_br_nfe_send_sefaz(osv.Model):
    """ Classe para salvar o retorno dos metodos de envio de cancelamento, inutilização e recepção de nota """
    _name = 'l10n_br_nfe.send_sefaz'
    _description = 'Envia os dados para o SEFAZ NFe'
    _columns = {                
        'name': fields.char('Nome', size=255),
        'file': fields.binary('Xml processado', readonly=True),        
        'state': fields.selection(
            [('init', 'init'), ('done', 'done')], 'state', readonly=True),
        'start_date': fields.datetime('Inicio'),
        'end_date': fields.datetime('Fim'),
        'nfe_environment': fields.selection(
            [('1', u'Produção'), ('2', u'Homologação')], 'Ambiente'),        
        'nfe_export_result': fields.one2many(
            'l10n_br_nfe.send_sefaz_result', 'send_sefaz_id',
            'NFe Export Result'),        
    }
    _defaults = {
        'state': 'init',        
        'nfe_environment': '2',        
    }


class l10n_br_nfe_send_sefaz_result(osv.Model):
    _name = 'l10n_br_nfe.send_sefaz_result'
    _columns = {
        'send_sefaz_id': fields.many2one(
            'l10n_br_nfe.send_sefaz', 'Envio SEFAZ',
            ondelete='cascade', select=True),
        'xml_type': fields.char('Tipo', size=255),
        'name':fields.char('Nome envio', size=255),                
        'file': fields.binary('Xml envio', readonly=True),
        'name_result':fields.char('Nome retorno', size=255),        
        'file_result': fields.binary('Xml retorno', readonly=True),        
        'status': fields.selection(
            [('success', 'Sucesso'), ('error', 'Erro')], 'Status'),
        'status_code':fields.char('Código',size=5),
        'message': fields.char('Mensagem', size=255),
    }
    
class res_company(osv.Model):
    _inherit = 'res.company'
    _columns = {
        'save_xml_folder': fields.boolean('Salvar Xml na Pasta?'),
    }


class l10n_br_account_invoice_invalid_number(osv.Model):
    _inherit = 'l10n_br_account.invoice.invalid.number'    
    _columns = {
        'invalidate_number_nfe_invoice_id': fields.many2one('l10n_br_nfe.send_sefaz', 'Inutilização numeração NFe'),            
        'state': fields.selection(
            [('draft', 'Rascunho'), ('not_authorized', 'Não autorizado'),('done', u'Autorizado Sefaz')], 'Status', required=True),        
        'status':fields.char('Status', size=10),
        'message':fields.char('Mensagem', size=200),
    }
    
    def action_draft_done(self, cr, uid, ids, *args):
        try:
            processo = self.send_request_to_sefaz(cr, uid, ids , args)
            
            if processo.resposta.infInut.cStat.valor == '102':
                self.write(cr, uid, ids, {'state': 'done', 'status':'102', 'message':processo.resposta.infInut.xMotivo.valor})
            else:
                self.write(cr, uid, ids, {'state':'not_authorized', 'status':processo.resposta.infInut.cStat.valor,
                        'message':processo.resposta.infInut.xMotivo.valor})
                
        except orm.except_orm, ex:
            raise ex          
        except Exception,e:
            raise orm.except_orm(_('Error !'), e.message)       
        return True
            
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

#--- Validation methods used before send any data to SEFAZ


