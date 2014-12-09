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

import datetime
import logging
from openerp import netsvc
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.addons.nfe.sped.nfe.validator.config_check import *
from openerp.addons.nfe.sped.nfe.processing.xml import invalidate
from dbus.bus import _logger
from sys import exc_info

_logger = logging.getLogger(__name__)

class L10n_brAccountInvoiceInvalidNumber(orm.Model):
    _inherit = 'l10n_br_account.invoice.invalid.number'
    _columns = {
        'state': fields.selection([
            ('draft', 'Rascunho'),
            ('not_authorized', 'Não autorizado'),
            ('done', u'Autorizado Sefaz')], 'Status', required=True),
        'status': fields.char('Status', size=10, readonly=True),
        'message': fields.char('Mensagem', size=200, readonly=True),
        'invalid_number_document_event_ids': fields.one2many(
            'l10n_br_account.document_event', 'document_event_ids',
            u'Eventos', states={'done':[('readonly',True)]}),
    }

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

    def action_draft_done(self, cr, uid, ids, context=None, *args):
        try:
            processo = self.send_request_to_sefaz(cr, uid, ids, args)
            values = {
                'message': processo.resposta.infInut.xMotivo.valor,
            }

            if processo.resposta.infInut.cStat.valor == '102':
                values['state'] = 'done'
                values['status'] = '102'
                self.write(cr, uid, ids, values, context=context)
                # context['caminho'] = processo.arquivos[0]['arquivo']
                self.attach_file_event(cr, uid, ids, None, 'inu', 'xml', context)
            else:
                values['state'] = 'not_authorized'
                values['status'] = processo.resposta.infInut.cStat.valor
                self.write(cr, uid, ids, values, context=context)

        except orm.except_orm, ex:
            raise ex
        except Exception, e:
            raise orm.except_orm(_('Error !'), e.message)
        return True

    def send_request_to_sefaz(self, cr, uid, ids, *args):
        for item in self.browse(cr, uid, ids):
            company_pool = self.pool.get('res.company')
            company = company_pool.browse(cr, uid, item.company_id.id)
            
            event_obj = self.pool.get('l10n_br_account.document_event')
            
            validate_nfe_configuration(company)
            validate_nfe_invalidate_number(company, item)
                
            results = []   
            try:                
                processo = invalidate(company, item) 
                vals = {
                            'type': str(processo.webservice),
                            'status': processo.resposta.infInut.cStat.valor,
                            'response': '',
                            'company_id': company.id,
                            'origin': '[INU] {0} - {1}'.format(str(item.number_start), str(item.number_end)),
                        #    'file_sent': processo.arquivos[0]['arquivo'],
                        #    'file_returned': processo.arquivos[1]['arquivo'],
                            'message': processo.resposta.infInut.xMotivo.valor,
                            'state': 'done',
                            'document_event_ids': item.id}
                results.append(vals)
                           
            except Exception as e:
                _logger.error(e.message,exc_info=True)
                vals = {
                        'type': '-1',
                        'status': '000',
                        'response': 'response',
                        'company_id': company.id,
                        'origin': '[INU] {0} - {1}'.format(str(item.number_start), str(item.number_end)),
                        'file_sent': 'False',
                        'file_returned': 'False',
                        'message': 'Erro desconhecido ' + e.message,
                        'state': 'done',
                        'document_event_ids': item.id
                        }
                results.append(vals)
            finally:
                for result in results:
                    event_obj.create(cr, uid, result)                
            return processo


class L10n_brAccountInvoiceCancel(orm.Model):
    _inherit = 'l10n_br_account.invoice.cancel'
    
    def action_draft_done(self, cr, uid, ids, *args):
        if len(ids) == 1:
            record = self.browse(cr, uid, ids[0])             
            wf_service = netsvc.LocalService('workflow')            
            wf_service.trg_validate(uid, 'account.invoice', \
                        record.invoice_id.id, 'invoice_cancel', cr)
            
            self.write(cr, uid, ids, {'state': 'done'})
        else:
            raise orm.except_orm(_('Error !'), u'Você pode cancelar apenas uma fatura por vez.')
        return True


class L10n_brDocumentEvent(orm.Model):
    _inherit = 'l10n_br_account.document_event'

    def set_done(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        values = {'state': 'done', 'end_date': datetime.datetime.now()}
        self.write(cr, uid, ids, values, context=context)
        return True



