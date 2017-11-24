# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, models
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFCE,
)


_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)

from .versao_nfe_padrao import ClasseVol


class SpedDocumentoVolume(models.Model):
    _inherit = 'sped.documento.volume'

    def monta_nfe(self):
        self.ensure_one()

        if self.documento_id.modelo != MODELO_FISCAL_NFE and \
                self.documento_id.modelo != MODELO_FISCAL_NFCE:
            return

        vol = ClasseVol()

        vol.qVol.valor = str(D(self.quantidade or 0))
        vol.esp.valor = self.especie or ''
        vol.marca.valor = self.marca or ''
        vol.nVol.valor = self.numero or ''
        vol.pesoL.valor = str(D(self.peso_liquido or 0).quantize(D('0.001')))
        vol.pesoB.valor = str(D(self.peso_bruto or 0).quantize(D('0.001')))

        return vol
