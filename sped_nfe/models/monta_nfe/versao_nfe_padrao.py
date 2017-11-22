# -*- coding: utf-8 -*-
#
# Copyright 2017 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

_logger = logging.getLogger(__name__)

try:
    from pysped.nfe.leiaute import *

except (ImportError, IOError) as err:
    _logger.debug(err)


ClasseProcNFe = ProcNFe_400
#
# Cabeçalho
#
ClasseNFe = NFe_400
ClasseNFCe = NFCe_400

#
# Itens
#
ClasseDet = Det_400
ClasseRastro = Rastro_400
ClasseDI = DI_400
ClasseAdi = Adi_400

#
# Transporte
#
ClasseReboque = Reboque_400
ClasseVol = Vol_400

#
# Documentos referenciados
#
ClasseNFRef = NFRef_400

#
# Parcelamento e pagamento
#
ClasseDup = Dup_400
ClassePag = Pag_400
