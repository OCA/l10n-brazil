# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2014  Luis Felipe Mileo - KMEE, www.kmee.com.br
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from openerp.osv import orm
from openerp.tools.translate import _
from openerp.addons.nfe.sped.nfe.processing.xml import check_key_nfe


class L10n_brAccountDocumentStatusSefaz(orm.TransientModel):

    _inherit = 'l10n_br_account_product.document_status_sefaz'

    def get_document_status(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, [], context=context)[0]
        # Call some method from l10n_br_account to check chNFE
        if context.get('company_id', False):
            company = context['company_id']
        else:
            company = self.pool.get('res.users').browse(
                cr, uid, uid,
                context=context).company_id

        chave_nfe = str(data['chNFe'])

        try:
            processo = check_key_nfe(company, chave_nfe)

            call_result = {
                'version': processo.resposta.versao.txt,
                'xMotivo': processo.resposta.cStat.txt + ' - ' +
                processo.resposta.xMotivo.txt,
                'cUF': processo.resposta.cUF.txt,
                'chNFe': processo.resposta.chNFe.txt,
                'nfe_environment': processo.resposta.tpAmb.txt,
                'protNFe': '' if processo.resposta.protNFe is None else
                processo.resposta.protNFe.infProt.nProt.txt,
                'retCancNFe': '',
                'procEventoNFe': '',
                'state': 'done',
            }

            self.write(cr, uid, ids, call_result)
        except Exception as e:
            raise orm.except_orm(
                _(u'Erro na consulta da chave!'), e)

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(
            cr, uid, 'l10n_br_account_product',
            'action_l10n_br_account_product_document_status_sefaz')
        res_id = result and result[1] or False
        result = act_obj.read(cr, uid, res_id, context=context)
        result['res_id'] = ids[0]
        return result
