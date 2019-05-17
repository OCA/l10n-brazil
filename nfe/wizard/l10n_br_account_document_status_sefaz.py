# -*- coding: utf-8 -*-
# Copyright (C) 2015  Luis Felipe Mileo - KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api
from odoo.osv import orm
from odoo.tools.translate import _
from ..sped.nfe.processing.xml import check_key_nfe


class L10nBrAccountDocumentStatusSefaz(models.TransientModel):

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
