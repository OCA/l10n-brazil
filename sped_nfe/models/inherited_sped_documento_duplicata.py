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
    from pysped.nfe.leiaute import (
        Dup_310,
    )
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumentoDuplicata(models.Model):
    _inherit = 'sped.documento.duplicata'

    def monta_nfe(self):
        self.ensure_one()

        if self.documento_id.modelo != MODELO_FISCAL_NFE and \
                self.documento_id.modelo != MODELO_FISCAL_NFCE:
            return

        dup = Dup_310()
        dup.nDup.valor = self.numero
        dup.dVenc.valor = self.data_vencimento
        dup.vDup.valor = str(D(self.valor))

        return dup
