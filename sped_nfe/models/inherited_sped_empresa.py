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

    @property
    def caminho_sped(self):
        filestore = config.filestore(self._cr.dbname)
        return os.path.join(filestore, 'sped', limpa_formatacao(self.cnpj_cpf))
