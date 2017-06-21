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
    from pysped.nfe.leiaute import (
        Pag_310,
    )
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.inscricao import limpa_formatacao

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumentoPagamento(models.Model):
    _inherit = 'sped.documento.pagamento'

    def monta_nfe(self):
        self.ensure_one()

        if self.documento_id.modelo != MODELO_FISCAL_NFE and \
                self.documento_id.modelo != MODELO_FISCAL_NFCE:
            return

        pag = Pag_310()
        pag.tPag.valor = self.forma_pagamento
        pag.vPag.valor = str(D(self.valor))
        # Troco somente na NF-e 4.00
        # pag.vTroco.valor = str(D(self.troco))

        if self.forma_pagamento in FORMA_PAGAMENTO_CARTOES:
            pag.card.CNPJ.valor = limpa_formatacao(self.cnpj_cpf or '')
            pag.card.tBand.valor = self.bandeira_cartao
            pag.card.cAut.valor = self.integracao_cartao

        return pag
