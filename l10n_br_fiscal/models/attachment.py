# -*- coding: utf-8 -*-
#
# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

import ntpath
import os
import shutil
import tarfile

from odoo.exceptions import UserError
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class Attachment(models.TransientModel):
    _name = 'l10n_br_fiscal.attachment'
    _description = "Fiscal Attachment"

    attachment = fields.Binary(
        string='Attachment',
        readonly=True,
    )
    file_name = fields.Char(
        string='Filename',
        default='attachments',
    )
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string='Attachments',
    )

    @api.multi
    def build_compressed_attachment(self, record_ids=None):
        '''

        Compacta os anexos recebidos e os retorno como um novo único anexo

        Outra maneira de utilizar o método é instanciar a classe, relacionando
        os ir.attachments requeridos com o campo attachment_ids, chamando o
        método sem a necessidade de nenhum parâmetro

        :param record_ids: Pode ser uma lista de quaisquer records contendo
        anexos ou uma lista de ir.attachments.
        Pode ser também um recordset com várias records quaiquer contendo
        anexos ou ir.attachments
        No caso de uma lista de records que não sejam do tipo ir.attachment,
        o método retornará TODOS os anexos dessas records compactadas em um
        arquivo.

        :return:
        Um record do tipo ir.attachment contendo todos os anexos recebidos
        compactados em um único arquivo.
        '''

        attachment_obj = self.env['ir.attachment']
        config_obj = self.env['ir.config_parameter']

        if record_ids:
            attachment_ids = record_ids

            if type(record_ids) is list and len(record_ids):
                attachs = self.env[record_ids[0]._name]
                for record in record_ids:
                    attachs += record
                attachment_ids = attachs

            if attachment_ids._name != 'ir.attachment':
                ids = attachment_obj
                for record in attachment_ids:
                    ids += \
                        attachment_obj.search([('res_id', '=', record.id)])
                attachment_ids = ids

            self.attachment_ids = attachment_ids

        attachment_ids = self.attachment_ids

        filestore_path = os.path.join(attachment_obj._filestore(), '')
        attachment_dir = filestore_path + 'attachments'

        # Cria o diretório e move seu conteúdo
        if not os.path.exists(attachment_dir):
            os.makedirs(attachment_dir)
        else:
            shutil.rmtree(attachment_dir)
            os.makedirs(attachment_dir)

        file_name = 'attachments'
        config_ids = config_obj.search([('key', '=', 'web.base.url')])

        attachment_obj.search([('active', '=', False)]).unlink()

        if len(config_ids):
            value = config_ids[0].value
            active_model = 'ir.attachment'
            active_id = self.id

            # tar_dir = attachment_dir + '/' + file_name
            tar_dir = os.path.join(attachment_dir, file_name)
            tFile = tarfile.open(tar_dir, 'w:gz')

            if value and active_id and active_model:
                # alterando o diretório de trabalho, caso contrário o arquivo
                # será misturado com os arquivos do diretório pai
                original_dir = os.getcwd()
                filter_attachments = []
                for attach in attachment_ids:
                    if attach.active:
                        filter_attachments.append(attach.id)
                if not filter_attachments:
                    raise UserError(_("No attachment to download"))

                for attachment in attachment_obj.browse(filter_attachments):
                    # caminho do arquivo
                    full_path = attachment_obj._full_path(
                        attachment.store_fname)
                    attachment_name = attachment.datas_fname
                    new_file = os.path.join(attachment_dir, attachment_name)

                    # copying in a new directory with a new name
                    # shutil.copyfile(full_path, new_file)
                    try:
                        shutil.copy2(full_path, new_file)
                    except:
                        pass
                        # raise UserError(_("Not Proper file name to download"))

                    head, tail = ntpath.split(new_file)
                    # change working directory otherwise it tars all parent directory
                    os.chdir(head)
                    try:
                        tFile.add(tail)
                    except:
                        _logger.error("No such file was found : %s" % tail)

                tFile.close()
                os.chdir(original_dir)

                values = {
                    'name': file_name + '.tar.gz',
                    'datas_fname': file_name + '.tar.gz',
                    'res_model': 'l10n_br_fiscal.attachment',
                    'res_id': self.id,
                    'type': 'binary',
                    'store_fname': 'attachments/attachments',
                    'active': False,
                }
                attachment_id = self.env['ir.attachment'].create(values)

                return attachment_id

        return False
