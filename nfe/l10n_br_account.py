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
from os.path import expanduser
from sped.nfe.validator.config_check import *

# class l10n_br_nfe_send_sefaz(osv.Model):
#     """ Classe para salvar o retorno dos metodos de envio de cancelamento, inutilização e recepção de nota """
#     _name = 'l10n_br_nfe.send_sefaz'
#     _description = 'Envia os dados para o SEFAZ NFe'
#     _columns = {                
#         'name': fields.char('Nome', size=255),
#         'file': fields.binary('Xml processado', readonly=True),        
#         'state': fields.selection(
#             [('init', 'init'), ('done', 'done')], 'state', readonly=True),
#         'start_date': fields.datetime('Inicio'),
#         'end_date': fields.datetime('Fim'),
#         'nfe_environment': fields.selection(
#             [('1', u'Produção'), ('2', u'Homologação')], 'Ambiente'),        
#         'nfe_export_result': fields.one2many(
#             'l10n_br_nfe.send_sefaz_result', 'send_sefaz_id',
#             'NFe Export Result'),        
#     }
#     _defaults = {
#         'state': 'init',        
#         'nfe_environment': '2',        
#     }


# class l10n_br_nfe_send_sefaz_result(osv.Model):
#     _name = 'l10n_br_nfe.send_sefaz_result'
#     _columns = {
#         'send_sefaz_id': fields.many2one(
#             'l10n_br_nfe.send_sefaz', 'Envio SEFAZ',
#             ondelete='cascade', select=True),
#         'xml_type': fields.char('Tipo', size=255),
#         'name':fields.char('Nome envio', size=255),                
#         'file': fields.binary('Xml envio', readonly=True),
#         'name_result':fields.char('Nome retorno', size=255),        
#         'file_result': fields.binary('Xml retorno', readonly=True),        
#         'status': fields.selection(
#             [('success', 'Sucesso'), ('error', 'Erro')], 'Status'),
#         'status_code':fields.char('Código',size=5),
#         'message': fields.char('Mensagem', size=255),
#     }
    
# class res_company(osv.Model):
#     _inherit = 'res.company'
#     _columns = {
#         'save_xml_folder': fields.boolean('Salvar Xml na Pasta?'),
#     }


class l10n_br_account_invoice_invalid_number(osv.Model):
    _inherit = 'l10n_br_account.invoice.invalid.number'    
    _columns = {
        # 'invalidate_number_nfe_invoice_id': fields.many2one('l10n_br_nfe.send_sefaz', 'Inutilização numeração NFe'),            
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

class L10n_brAccountInvoiceCancel(orm.Model):

    _inherit = 'l10n_br_account.invoice.cancel'

    def action_draft_done(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'done'})
        return True

class L10n_brDocumentEvent(orm.Model):

    _inherit = 'l10n_br_account.document_event'

    def set_done(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        self.write(cr, uid, ids, {'state':'done', 'end_date': datetime.datetime.now()}, context=context)
        return True
        
#--- Validation methods used before send any data to SEFAZ


