# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013 Luis Felipe Miléo - luisfelipe@mileo.co                  #
# Copyright (C) 2014 Renato Lima - Akretion                                   #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp.osv import orm, fields


class L10n_brAccountDocumentStatusSefaz(orm.TransientModel):
    """ Check fiscal document key"""
    _name = 'l10n_br_account_product.document_status_sefaz'
    _description = 'Check fiscal document key on sefaz'
    _columns = {
        'state': fields.selection(
            [('init', 'Init'),
             ('error', 'Error'),
             ('done', 'Done')], 'State', select=True, readonly=True),
        'version': fields.text(u'Versão', readonly=True),
        'nfe_environment': fields.selection(
            [('1', u'Produção'), ('2', u'Homologação')], 'Ambiente'),
        'xMotivo': fields.text('Motivo', readonly=True),
        # FIXME
        'cUF': fields.integer('Codigo Estado', readonly=True),
        'chNFe': fields.char('Chave de Acesso NFE', size=44),
        'protNFe': fields.text('Protocolo NFE', readonly=True),
        'retCancNFe': fields.text('Cancelamento NFE', readonly=True),
        'procEventoNFe': fields.text('Processamento Evento NFE',
                                     readonly=True),
    }
    _defaults = {
        'state': 'init',
    }

    def get_document_status(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, [], context=context)[0]
        # Call some method from l10n_br_account to check chNFE
        call_result = {
            'version': '2.01',
            'nfe_environment': '2',
            'xMotivo': '101',
            'cUF': 27,
            'chNFe': data['chNFe'],
            'protNFe': '123',
            'retCancNFe': '',
            'procEventoNFe': '',
            'state': 'done',
            }
        self.write(cr, uid, ids, call_result)
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(
            cr, uid, 'l10n_br_account_product',
            'action_l10n_br_account_product_document_status_sefaz')
        res_id = result and result[1] or False
        result = act_obj.read(cr, uid, res_id, context=context)
        result['res_id'] = ids[0]
        return result
