# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

import logging
from odoo import api, fields, models
from ...sped.constante_tributaria import *

_logger = logging.getLogger(__name__)

try:
    from pysped.nfe import ProcessadorNFe
    from pysped.nfe.webservices_flags import *
    from pysped.nfe.leiaute import *
    from pybrasil.inscricao import limpa_formatacao
    from pybrasil.data import parse_datetime, UTC

except (ImportError, IOError) as err:
    _logger.debug(err)


class DocumentoVolume(models.Model):
    _inherit = 'sped.documento.volume'

    def monta_nfe(self):
        self.ensure_one()

        if self.documento_id.modelo != MODELO_FISCAL_NFE and \
                self.documento_id.modelo != MODELO_FISCAL_NFCE:
            return

        vol = Vol_310()

        vol.qVol.valor = str(D(self.quantidade or 0))
        vol.esp.valor = self.especie or ''
        vol.marca.valor = self.marca or ''
        vol.nVol.valor = self.numero or ''
        vol.pesoL.valor = str(D(self.peso_liquido or 0).quantize(D('0.001')))
        vol.pesoB.valor = str(D(self.peso_bruto or 0).quantize(D('0.001')))

        return vol
