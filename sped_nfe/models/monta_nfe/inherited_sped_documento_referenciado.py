# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# Copyright 2016 KMEE INFORMATICA LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_CFE,
    MODELO_FISCAL_CTE,
    MODELO_FISCAL_CUPOM_FISCAL_ECF,
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.inscricao import limpa_formatacao
    from pybrasil.data import parse_datetime, UTC

except (ImportError, IOError) as err:
    _logger.debug(err)

from ..versao_nfe_padrao import ClasseNFRef


class SpedDocumentoReferenciado(models.Model):
    _inherit = 'sped.documento.referenciado'

    def monta_nfe(self):
        self.ensure_one()

        if self.documento_id.modelo != MODELO_FISCAL_NFE and \
                self.documento_id.modelo != MODELO_FISCAL_NFCE:
            return

        docref = ClasseNFRef()

        if self.modelo in (
                MODELO_FISCAL_NFE,
                MODELO_FISCAL_NFCE,
                MODELO_FISCAL_CFE,
        ):
            docref.refNFe.valor = self.chave

        elif self.modelo == MODELO_FISCAL_CTE:
            docref.refCTe.valor = self.chave

        elif self.modelo == MODELO_FISCAL_CUPOM_FISCAL_ECF:
            docref.refECF.mod.valor = self.modelo
            docref.refECF.nECF.valor = self.numero_ecf
            docref.refECF.nCOO.valor = self.numero_coo

        return docref
