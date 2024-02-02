#
# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

import logging
import ntpath
import os
import shutil
import tarfile

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Attachment(models.TransientModel):
    _name = "l10n_br_fiscal.attachment"
    _description = "Fiscal Document Attachment"

    attachment = fields.Binary(readonly=True)

    file_name = fields.Char(default="attachments")

    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        string="Attachments",
    )

    @api.model
    def build_compressed_attachment(self, record_ids=None):
        """
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
        """

        attachment_obj = self.env["ir.attachment"]
        file_name = "attachments"

        self.attachment_ids = self._records_to_attachments(record_ids)

        filestore_path = os.path.join(attachment_obj._filestore(), "")
        attachment_dir = filestore_path + "attachments"

        if os.path.exists(attachment_dir):
            shutil.rmtree(attachment_dir)
        os.makedirs(attachment_dir)

        original_dir = os.getcwd()

        for attachment in self.attachment_ids:
            full_path = attachment_obj._full_path(attachment.store_fname)
            new_file = os.path.join(attachment_dir, attachment.store_fname)

            shutil.copy2(full_path, new_file)
            head, tail = ntpath.split(new_file)
            os.chdir(head)

            tFile = tarfile.open(os.path.join(attachment_dir, file_name), "w:gz")
            try:
                tFile.add(tail)
            except Exception:
                _logger.error("No such file was found : %s" % tail)

            tFile.close()

        os.chdir(original_dir)

        return self.env["ir.attachment"].create(
            {
                "name": file_name + ".tar.gz",
                "res_model": "l10n_br_fiscal.attachment",
                "res_id": self.id,
                "type": "binary",
                "store_fname": "attachments/attachments",
            }
        )

    @api.model
    def _records_to_attachments(self, record_ids):
        attachment_obj = self.env["ir.attachment"]
        attachment_ids = record_ids

        if isinstance(record_ids, list) and len(record_ids):
            attachs = self.env[record_ids[0]._name]
            for record in record_ids:
                attachs += record
            attachment_ids = attachs

        if attachment_ids._name != "ir.attachment":
            ids = attachment_obj
            for record in attachment_ids:
                ids += attachment_obj.search([("res_id", "=", record.id)])
            attachment_ids = ids

        return attachment_ids
