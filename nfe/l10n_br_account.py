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
from openerp.osv import orm, fields
from openerp.tools.translate import _
from sped.nfe.validator.config_check import *


class L10n_brAccountInvoiceInvalidNumber(orm.Model):
    _inherit = 'l10n_br_account.invoice.invalid.number'
    _columns = {
        'state': fields.selection([
            ('draft', 'Rascunho'),
            ('not_authorized', 'Não autorizado'),
            ('done', u'Autorizado Sefaz')], 'Status', required=True),
        'status': fields.char('Status', size=10),
        'message': fields.char('Mensagem', size=200),
    }

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
            else:
                values['state'] = 'not_authorized'
                values['status'] = processo.resposta.infInut.cStat.valor
                self.write(cr, uid, ids, values, context=context)

        except orm.except_orm, ex:
            raise ex
        except Exception, e:
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
        values = {'state': 'done', 'end_date': datetime.datetime.now()}
        self.write(cr, uid, ids, values, context=context)
        return True



