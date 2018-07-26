# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from openerp.exceptions import ValidationError


class S3000ExclusaoWizard(models.TransientModel):
    _name = 's3000.exclusao.wizard'

    motivo = fields.Text(
        string='Motivo',
    )

    @api.multi
    def create_s3000(self):
        self.ensure_one()
        """
        Criar o registro de Exclusão relacionado com o registro original
        :return:
        """
        if not self.motivo:
            raise ValidationError("Por favor digite o motivo da exclusão deste registro!")
        sped_registro_id = self.env['sped.registro'].browse(self.env.context['active_id'])
        sped_registro_id.motivo_s3000 = self.motivo
        sped_s3000 = sped_registro_id.excluir_registro()
        sped_registro_id.sped_s3000 = sped_s3000