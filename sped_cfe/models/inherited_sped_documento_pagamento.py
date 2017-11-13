# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#   Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging
from odoo import api, models
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL_CFE,
    FORMA_PAGAMENTO_CARTOES,
)

_logger = logging.getLogger(__name__)

try:
    from satcfe import *
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.inscricao import limpa_formatacao
    from satcfe.entidades import MeioPagamento

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumentoPagamento(models.Model):
    _inherit = 'sped.documento.pagamento'

    def monta_cfe(self):
        self.ensure_one()

        kwargs = {}

        if self.documento_id.modelo != MODELO_FISCAL_CFE:
            return

        if self.forma_pagamento in FORMA_PAGAMENTO_CARTOES:
            # pag.card.CNPJ.valor = limpa_formatacao(self.cnpj_cpf or '')
            # pag.card.tBand.valor = self.bandeira_cartao
            kwargs['cAdmC'] = self.integracao_cartao

        pagamento = MeioPagamento(
            cMP='01',
                    # self.forma_pagamento,
            vMP=D(self.valor).quantize(D('0.0001')),
            **kwargs
        )
        pagamento.validar()

        return pagamento

