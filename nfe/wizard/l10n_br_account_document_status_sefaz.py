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

from openerp import models, api
from openerp.osv import orm
from openerp.tools.translate import _
from openerp.addons.nfe.sped.nfe.processing.xml import check_key_nfe


class L10n_brAccountDocumentStatusSefaz(models.TransientModel):

    _inherit = 'l10n_br_account_product.document_status_sefaz'

    @api.multi
    def get_document_status(self):
        chave_nfe = self.chNFe

        try:
            processo = check_key_nfe(self.write_uid.company_id, chave_nfe)

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

            self.write(call_result)
        except Exception as e:
            # fixme:
            raise orm.except_orm(
                _(u'Erro na consulta da chave!'), e)

        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        result = mod_obj.get_object_reference('l10n_br_account_product',
                                              'action_l10n_br_account_product'
                                              '_document_status_sefaz')
        res_id = result and result[1] or False
        result = act_obj.browse(res_id)
        result['res_id'] = self.id
        return result
