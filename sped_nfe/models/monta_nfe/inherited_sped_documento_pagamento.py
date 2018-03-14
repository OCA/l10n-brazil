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
    FORMA_PAGAMENTO_CARTOES,
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.inscricao import limpa_formatacao
    from pysped.nfe.leiaute import DetPag_400

except (ImportError, IOError) as err:
    _logger.debug(err)

from ..versao_nfe_padrao import ClassePag


class SpedDocumentoPagamento(models.Model):
    _inherit = 'sped.documento.pagamento'

    def monta_nfe(self):
        self.ensure_one()

        if self.documento_id.modelo != MODELO_FISCAL_NFE and \
                self.documento_id.modelo != MODELO_FISCAL_NFCE:
            return

        det_pag = DetPag_400()
        det_pag.tPag.valor = self.forma_pagamento
        det_pag.vPag.valor = str(D(self.valor))

        if self.forma_pagamento in FORMA_PAGAMENTO_CARTOES:
            det_pag.card.CNPJ.valor = limpa_formatacao(
                self.participante_id.cnpj_cpf or '')
            det_pag.card.tBand.valor = self.bandeira_cartao
            det_pag.card.cAut.valor = self.numero_aprovacao
            det_pag.card.tpIntegra.valor = self.integracao_cartao

        return det_pag
