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
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
)

_logger = logging.getLogger(__name__)

try:
    from pysped.nfe.leiaute import (
        Adi_310,
        DI_310,
    )
    from pybrasil.inscricao import limpa_formatacao
    from pybrasil.data import parse_datetime, UTC
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumentoItemDeclaracaoImportacao(models.Model):
    _inherit = 'sped.documento.item.declaracao.importacao'

    def monta_nfe(self):
        self.ensure_one()

        if self.documento_id.modelo != MODELO_FISCAL_NFE and \
                self.documento_id.modelo != MODELO_FISCAL_NFCE:
            return

        di = DI_310()

        di.nDI.valor = self.numero_documento
        di.dDI.valor = self.data_registro[:10]
        di.xLocDesemb.valor = self.local_desembaraco
        di.UFDesemb.valor = self.uf_desembaraco_id.uf
        di.dDesemb.valor = self.data_desembaraco[:10]
        di.tpViaTransp.valor = self.via_trans_internacional
        di.vAFRMM.valor = D(self.vr_afrmm)
        di.tpIntermedio.valor = self.forma_importacao

        if self.participante_id:
            di.CNPJ.valor = limpa_formatacao(self.participante_id.cnpj_cpf)
            di.UFTerceiro.valor = self.participante_id.estado
            di.cExportador.valor = \
                limpa_formatacao(self.participante_id.cnpj_cpf)

        #
        # Sempre existe pelo menos uma adição
        #
        adi = Adi_310()

        adi.nAdicao.valor = self.numero_adicao
        adi.nSeqAdic.valor = self.sequencial

        if self.participante_id:
            adi.cFabricante.valor = \
                limpa_formatacao(self.participante_id.cnpj_cpf)

        adi.vDescDI.valor = D(self.vr_desconto)
        adi.nDraw.valor = self.numero_drawback

        di.adi.append(adi)

        #
        # Agora, se houver mais
        #
        for adicao in self.adicao_ids:
            adi = Adi_310()

            adi.nAdicao.valor = adicao.numero_adicao
            adi.nSeqAdic.valor = adicao.sequencial

            if self.participante_id:
                adi.cFabricante.valor = \
                    limpa_formatacao(self.participante_id.cnpj_cpf)

            adi.vDescDI.valor = D(adicao.vr_desconto)
            adi.nDraw.valor = adicao.numero_drawback

            di.adi.append(adi)

        return di
