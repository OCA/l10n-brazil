# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

import logging
import os
from odoo import api, fields, models, _, exceptions
from odoo.tools import config

_logger = logging.getLogger(__name__)

try:
    from pysped.nfe import ProcessadorNFe
    from pybrasil.inscricao import limpa_formatacao

except (ImportError, IOError) as err:
    _logger.debug(err)


class Empresa(models.Model):
    _inherit = 'sped.empresa'

    certificado_id = fields.Many2one(
        comodel_name='sped.certificado',
        string=u'Certificado digital',
    )
    logo_danfe = fields.Binary(
        string=u'Logo no DANFE',
        attachment=True,
    )
    logo_danfce = fields.Binary(
        string=u'Logo no DANFCE',
        attachment=True,
    )
    mail_template_nfe_autorizada_id = fields.Many2one(
        comodel_name='mail.template',
        string=u'Modelo de email para NF-e autorizada',
        #domain=[('model_id', '=', ref('sped.model_sped_documento'))],
    )
    mail_template_nfe_cancelada_id = fields.Many2one(
        comodel_name='mail.template',
        string=u'Modelo de email para NF-e cancelada',
        #domain=[('model_id', '=', ref('sped.model_sped_documento'))],
    )
    mail_template_nfe_denegada_id = fields.Many2one(
        comodel_name='mail.template',
        string=u'Modelo de email para NF-e denegada',
        #domain=[('model_id', '=', ref('sped.model_sped_documento'))],
    )
    mail_template_nfe_cce_id = fields.Many2one(
        comodel_name='mail.template',
        string=u'Modelo de email para CC-e',
        #domain=[('model_id', '=', ref('sped.model_sped_documento'))],
    )
    mail_template_nfce_autorizada_id = fields.Many2one(
        comodel_name='mail.template',
        string=u'Modelo de email para NFC-e autorizada',
        #domain=[('model_id', '=', ref('sped.model_sped_documento'))],
    )
    mail_template_nfce_cancelada_id = fields.Many2one(
        comodel_name='mail.template',
        string=u'Modelo de email para NFC-e cancelada',
        #domain=[('model_id', '=', ref('sped.model_sped_documento'))],
    )
    mail_template_nfce_denegada_id = fields.Many2one(
        comodel_name='mail.template',
        string=u'Modelo de email para NFC-e denegada',
        #domain=[('model_id', '=', ref('sped.model_sped_documento'))],
    )
    mail_template_nfce_cce_id = fields.Many2one(
        comodel_name='mail.template',
        string=u'Modelo de email para CC-e',
        #domain=[('model_id', '=', ref('sped.model_sped_documento'))],
    )

    @property
    def caminho_sped(self):
        filestore = config.filestore(self._cr.dbname)
        return os.path.join(filestore, 'sped', limpa_formatacao(self.cnpj_cpf))

    def processador_nfe(self):
        self.ensure_one()

        processador = ProcessadorNFe()
        processador.estado = self.estado

        if self.certificado_id:
            processador.certificado = \
                self.certificado_id.certificado_nfe()

        return processador
