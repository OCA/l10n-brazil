# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
# Copyright (C) 2011  Vinicius Dittgen - PROGE, Leonardo Santagada - PROGE    #
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

import time
import base64
from osv import fields, osv
from tools.translate import _


class nfe_export_from_invoice(osv.TransientModel):
    """ Export fiscal eletronic file from invoice"""
    _name = "l10n_br_account.nfe_export_from_invoice"
    _description = "Export eletronic invoice for Emissor de NFe SEFAZ SP"
    _columns = {
        'name': fields.char('Nome', size=255),
        'file': fields.binary('Arquivo', readonly=True),
        'file_type': fields.selection([('xml', 'XML'),
                                       ('txt', ' TXT')], 'Tipo do Arquivo'),
        'state': fields.selection([('init', 'init'),
                                   ('done', 'done')],
                                  'state', readonly=True),
        'nfe_environment': fields.selection([('1', 'Produção'),
                                             ('2', 'Homologação')],
                                            'Ambiente')
    }
    _defaults = {
        'state': 'init',
        'file_type': 'txt',
        'nfe_environment': '1'
    }

    def nfe_export_from_invoice(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, [], context=context)[0]
        inv_obj = self.pool.get('account.invoice')
        active_ids = context.get('active_ids', [])
        export_inv_ids = []
        export_inv_numbers = []
        company_ids = []
        err_msg = ''

        for inv in inv_obj.browse(cr, uid, active_ids, context=context):
            if inv.state not in ('sefaz_export'):
                err_msg += u"O Documento Fiscal %s não esta definida para ser \
                exportação para a SEFAZ.\n" % inv.internal_number
            elif not inv.own_invoice:
                err_msg += u"O Documento Fiscal %s é do tipo externa e não \
                pode ser exportada para a receita.\n" % inv.internal_number
            else:
                inv_obj.write(cr, uid, [inv.id], {'nfe_export_date': False,
                                                  'nfe_access_key': False,
                                                  'nfe_status': False,
                                                  'nfe_date': False})

                message = "O Documento Fiscal %s foi \
                    exportada." % inv.internal_number
                inv_obj.log(cr, uid, inv.id, message)
                export_inv_ids.append(inv.id)
                company_ids.append(inv.company_id.id)

            export_inv_numbers.append(inv.internal_number)

        if len(set(company_ids)) > 1:
            err_msg += u'Não é permitido exportar Documentos \
            Fiscais de mais de uma empresa, por favor selecione Documentos \
            Fiscais da mesma empresa.'

        if export_inv_ids:
            if len(export_inv_numbers) > 1:
                name = 'nfes%s-%s.%s' % (
                    time.strftime('%d-%m-%Y'),
                    self.pool.get('ir.sequence').get(cr, uid, 'nfe.export'),
                    data['file_type'])
            else:
                name = 'nfe%s.%s' % (export_inv_numbers[0], data['file_type'])

            mod = __import__(
                'l10n_br_account.sped.nfe.serializer.' + data['file_type'],
                 globals(), locals(), data['file_type'])

            func = getattr(mod, 'nfe_export')
            nfe_file = func(cr, uid, export_inv_ids, data['nfe_environment'])

            self.write(cr, uid, ids, {'file': base64.b64encode(nfe_file),
                                      'state': 'done',
                                      'name': name}, context=context)

        if err_msg:
            raise osv.except_osv(_('Error !'), _("'%s'") % _(err_msg, ))

        return False
