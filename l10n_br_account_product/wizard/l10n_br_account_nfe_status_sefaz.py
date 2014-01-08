# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013 Luis Felipe Miléo - luisfelipe@mileo.co                  #
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

from openerp.osv import orm, fields
from openerp.tools.translate import _


class L10n_brAccountNfeStatusSefaz(orm.TransientModel):
    """ Check fiscal eletronic key"""
    _name = 'l10n_br_account_product.nfe_status_sefaz'
    _description = 'Check eletronic invoice key on sefaz'
    _columns = {
        'state':fields.selection([
            ('init','Init'),
            ('error','Error'),
            ('done','Done'),
        ],'State', select=True, readonly=True),
        'versao': fields.text(u'Versão', readonly=True),
        'tpAmbiente': fields.selection(
            [('1', u'Produção'), ('2', u'Homologação')], 'Ambiente'),
        'xMotivo': fields.text('Motivo', readonly=True),
        'cUF': fields.integer('Codigo Estado',readonly=True),#FIXME
        'chNFe': fields.char(
            'Chave de Acesso NFE', size=44),
        'protNFe': fields.text('Protocolo NFE',readonly=True),
        'retCancNFe': fields.text('Cancelamento NFE',readonly=True),
        'procEventoNFe': fields.text('Processamento Evento NFE',readonly=True),
    }
    _defaults = {
        'state': 'init',
    }

    def _get_invoice_ids(self, cr, uid, data, context=None):

        if not context:
            context = {}

        return context.get('active_ids', [])

    def nfe_status_sefaz(self, cr, uid, ids, context=None):

        #Call some method from l10n_br_account to check chNFE

        call_result = {
            'versao': '2.01',
            'tpAmbiente': '2',
            'xMotivo': '101',
            'cUF': 27,
            'chNFe': '123412341234123412341234123412341234',
            'protNFe': '123',
            'retCancNFe': '',
            'procEventoNFe': '',
            'state': 'done',
            }
        self.write(cr, uid, ids, call_result)
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'l10n_br_account_product', 'action_l10n_br_account_product_nfe_status_sefaz')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, id, context=context)
        result['res_id'] = ids[0]
        return result





# 
# class L10n_brAccountNfeStatusSefazResult(orm.TransientModel):
#     _name = 'l10n_br_account_product.nfe_status_sefaz_result'
#     _columns = {
#         'wizard_id': fields.many2one(
#             'l10n_br_account_product.nfe_status_sefaz', 'Wizard ID',
#             ondelete='cascade', select=True),
#         'document': fields.char('Documento', size=255),
#         'status': fields.selection(
#             [('success', 'Sucesso'), ('error', 'Erro')], 'Status'),
#         'message': fields.char('Mensagem', size=255),
#     }
