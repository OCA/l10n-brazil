# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#   Hugo Borges <hugo.borges@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import _, models, fields, api

import base64
import re
import gzip
import io
from lxml import objectify


class ImportaNFe(models.TransientModel):

    _name = 'sped.importa.nfe'
    _description = 'Importa NFe'

    chave = fields.Char(
        string='Chave',
        size=44,
        required=True,
    )

    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        required=True,
    )

    purchase_id = fields.Many2one(
        comodel_name='purchase.order',
    )

    @api.multi
    def importa_nfe(self, chave=None, empresa=None):
        self.ensure_one()
        empresa = self.empresa_id or empresa
        chave = self.chave or chave

        nfe_result = self.download_nfe(empresa, chave)

        if nfe_result['code'] == '138':

            nfe = objectify.fromstring(nfe_result['nfe'])
            documento = self.env['sped.documento'].new()
            documento.modelo = nfe.NFe.infNFe.ide.mod.text
            documento.le_nfe(xml=nfe_result['nfe'])
        else:
            raise models.ValidationError(_(
                nfe_result['code'] + ' - ' + nfe_result['message'])
            )
        if self.purchase_id:
            documento.purchase_order_ids = [(4, self.purchase_id.id)]
        return {
            'name': _("Importar NFe"),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'sped.documento',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': documento.id,
            'context': {'active_id': documento.id},
            'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}},
        }

    def download_nfe(self, empresa, chave):
        p = empresa.processador_nfe()
        cnpj_partner = re.sub('[^0-9]', '', empresa.cnpj_cpf)

        result = p.consultar_distribuicao(
            cnpj_cpf=cnpj_partner,
            chave_nfe=chave)

        if result.resposta.status == 200:  # Webservice ok
            if result.resposta.cStat.valor == '138':
                nfe_zip = \
                    result.resposta.loteDistDFeInt.docZip[0].docZip.valor
                orig_file_desc = gzip.GzipFile(
                    mode='r',
                    fileobj=io.StringIO(
                        base64.b64decode(nfe_zip))
                )
                nfe = orig_file_desc.read()
                orig_file_desc.close()

                return {
                    'code': result.resposta.cStat.valor,
                    'message': result.resposta.xMotivo.valor,
                    'file_sent': result.envio.xml,
                    'file_returned': result.resposta.xml,
                    'nfe': nfe,
                }
            else:
                return {
                    'code': result.resposta.cStat.valor,
                    'message': result.resposta.xMotivo.valor,
                    'file_sent': result.envio.xml,
                    'file_returned': result.resposta.xml
                }
        else:
            return {
                'code': result.resposta.status,
                'message': result.resposta.reason,
                'file_sent': result.envio.xml,
                'file_returned': None
            }
