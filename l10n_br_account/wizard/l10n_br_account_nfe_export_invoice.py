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
from openerp.osv import orm, fields
from openerp.tools.translate import _


class l10n_br_account_nfe_export_invoice(orm.TransientModel):
    """ Export fiscal eletronic file from invoice"""
    _name = 'l10n_br_account.nfe_export_invoice'
    _description = 'Export eletronic invoice for Emissor de NFe SEFAZ SP'
    _columns = {
        'name': fields.char('Nome', size=255),
        'file': fields.binary('Arquivo', readonly=True),
        'file_type': fields.selection(
            [('xml', 'XML'), ('txt', ' TXT')], 'Tipo do Arquivo'),
        'state': fields.selection(
            [('init', 'init'), ('done', 'done')], 'state', readonly=True),
        'nfe_environment': fields.selection(
            [('1', u'Produção'), ('2', u'Homologação')], 'Ambiente'),
        'sign_xml': fields.boolean('Assinar XML'),
        'nfe_export_result': fields.one2many(
            'l10n_br_account.nfe_export_invoice_result', 'wizard_id',
            'NFe Export Result'),
        'export_folder': fields.boolean(u'Salvar na Pasta de Exportação'),
    }
    _defaults = {
        'state': 'init',
        'file_type': 'txt',
        'nfe_environment': '1',
        'sign_xml': False,
        'export_folder': False,
    }

    def _get_invoice_ids(self, cr, uid, data, context=None):

        if not context:
            context = {}

        return context.get('active_ids', [])

    def nfe_export(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, [], context=context)[0]
        inv_obj = self.pool.get('account.invoice')
        active_ids = self._get_invoice_ids(cr, uid, data, context)
        export_inv_ids = []
        export_inv_numbers = []
        company_ids = []
        err_msg = ''

        if not active_ids:
            err_msg = u'Não existe nenhum documento fiscal para ser exportado!'

        for inv in inv_obj.browse(cr, uid, active_ids, context=context):
            if inv.state not in ('sefaz_export'):
                err_msg += u"O Documento Fiscal %s não esta definida para ser \
                exportação para a SEFAZ.\n" % inv.internal_number
            elif not inv.issuer == '0':
                err_msg += u"O Documento Fiscal %s é do tipo externa e não \
                pode ser exportada para a receita.\n" % inv.internal_number
            else:
                inv_obj.write(cr, uid, [inv.id], {'nfe_export_date': False,
                                                  'nfe_access_key': False,
                                                  'nfe_status': False,
                                                  'nfe_date': False})

                message = "O Documento Fiscal %s foi \
                    exportado." % inv.internal_number
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

            mod_serializer = __import__(
                'l10n_br_account.sped.nfe.serializer.' + data['file_type'],
                 globals(), locals(), data['file_type'])

            func = getattr(mod_serializer, 'nfe_export')
            nfes = func(
                cr, uid, export_inv_ids, data['nfe_environment'],
                '200', context)

            for nfe in nfes:
                #if nfe['message']:
                    #status = 'error'
                #else:
                    #status = 'success'

                #self.pool.get(self._name + '_result').create(
                    #cr, uid, {'document': nfe['key'],
                        #'message': nfe['message'],
                        #'status': status,
                        #'wizard_id': data['id']})

                nfe_file = nfe['nfe'].encode('utf8')

            self.write(
                cr, uid, ids, {'file': base64.b64encode(nfe_file),
                'state': 'done', 'name': name}, context=context)

        if err_msg:
            raise orm.except_orm(_('Error!'), _("'%s'") % _(err_msg, ))

        mod_obj = self.pool.get('ir.model.data')
        model_data_ids = mod_obj.search(
            cr, uid, [('model', '=', 'ir.ui.view'),
            ('name', '=', 'l10n_br_account_nfe_export_invoice_form')],
            context=context)
        resource_id = mod_obj.read(
            cr, uid, model_data_ids,
            fields=['res_id'], context=context)[0]['res_id']

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': data['id'],
            'views': [(resource_id, 'form')],
            'target': 'new',
        }


class l10n_br_account_nfe_export_invoice_result(orm.TransientModel):
    _name = 'l10n_br_account.nfe_export_invoice_result'
    _columns = {
        'wizard_id': fields.many2one(
            'l10n_br_account.nfe_export_invoice', 'Wizard ID',
            ondelete='cascade', select=True),
        'document': fields.char('Documento', size=255),
        'status': fields.selection(
            [('success', 'Sucesso'), ('error', 'Erro')], 'Status'),
        'message': fields.char('Mensagem', size=255),
    }
