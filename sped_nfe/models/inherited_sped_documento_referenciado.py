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


class DocumentoReferenciado(models.Model):
    _inherit = 'sped.documento.referenciado'

    def monta_nfe(self):
        self.ensure_one()

        if self.documento_id.modelo != MODELO_FISCAL_NFE and \
                self.documento_id.modelo != MODELO_FISCAL_NFCE:
            return

        docref = NFRef_310()

        if self.modelo in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE):
            docref.refNFe.valor = self.chave

        elif self.modelo == MODELO_FISCAL_CTE:
            docref.refCTe.valor = self.chave

        elif self.modelo == MODELO_FISCAL_CUPOM_FISCAL_ECF:
            docref.refECF.mod.valor = self.modelo
            docref.refECF.nECF.valor = self.numero_ecf
            docref.refECF.nCOO.valor = self.numero_coo

        return docref
