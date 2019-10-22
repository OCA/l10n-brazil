# -*- coding: utf-8 -*-
# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import base64

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..tools.misc import caminho_empresa

CODIGO_NOME = {
    '55': 'nfe',
}


class L10nBrAccountDocumentEvent(models.Model):
    _inherit = 'l10n_br_account.document_event'

    # Esses arquivos são somente para visualizacao
    xml_sent_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML',
        copy=False,
        readony=True,
    )
    xml_returned_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML de autorização',
        copy=False,
        readony=True,
    )

    @staticmethod
    def monta_caminho(ambiente, company_id, chave):
        caminho = caminho_empresa(company_id, chave[:2])

        if ambiente == 1:
            caminho = os.path.join(caminho, 'producao/')
        else:
            caminho = os.path.join(caminho, 'homologacao/')

        data = '20' + chave[2:4] + '-' + chave[4:6]
        serie = chave[22:25]
        numero = chave[25:34]

        caminho = os.path.join(caminho, data + '/')
        caminho = os.path.join(caminho, serie + '-' + numero + '/')

        try:
            os.makedirs(caminho)
        except:
            pass
        return caminho

    def _grava_arquivo_disco(self, arquivo, file_name):
        save_dir = self.monta_caminho(
            ambiente=int(self.company_id.nfe_environment),
            company_id=self.company_id,
            chave=self.document_event_ids.nfe_access_key,
        )
        file_path = os.path.join(save_dir, file_name)
        try:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            f = open(file_path, 'w')
        except IOError:
            raise UserError(
                _(u'Erro!'), _(u"""Não foi possível salvar o arquivo
                    em disco, verifique as permissões de escrita
                    e o caminho da pasta"""))
        else:
            f.write(arquivo)
            f.close()
        return file_path

    def _grava_anexo(self, arquivo, extensao_sem_ponto, autorizacao=False,
                     sequencia=False):
        self.ensure_one()

        file_name = ''
        file_name += self.document_event_ids.nfe_access_key
        file_name += '-'
        if autorizacao:
            file_name += 'proc-'
        if sequencia:
            file_name += str(sequencia) + '-'
        file_name += CODIGO_NOME[
            self.document_event_ids.fiscal_document_id.code
        ]
        file_name += '.' + extensao_sem_ponto

        file_path = self._grava_arquivo_disco(arquivo, file_name)

        ir_attachment_id = self.env['ir.attachment'].search(
            [
                ('res_model', '=', self._name),
                ('res_id', '=', self.id),
                ('name', '=', file_name),
            ]
        )
        ir_attachment_id.unlink()

        attachment_id = ir_attachment_id.create({
            'name': file_name,
            'datas_fname': file_name,
            'res_model': self._name,
            'res_id': self.id,
            'datas': base64.b64encode(arquivo),
            'mimetype': 'application/' + extensao_sem_ponto,
            'type': 'binary',
        })

        if autorizacao:
            vals = {
                'file_returned': file_path,
                'xml_returned_id': attachment_id.id,
            }
        else:
            vals = {
                'file_sent': file_path,
                'xml_sent_id': attachment_id.id,
            }
        self.write(vals)
        return attachment_id

    @api.multi
    def set_done(self, arquivo_xml):
        self._grava_anexo(arquivo_xml, 'xml', autorizacao=True)
        return self.write({
            'state': 'done',
            'end_date': fields.Datetime.now()
        })
