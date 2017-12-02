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
    # from pysped.nfe.leiaute import *
    from pysped.nfe.leiaute import (ProcNFe_400 as ProcNFe,
                                    NFe_400 as NFe,
                                    NFCe_400 as NFCe,
                                    Det_400 as Det,
                                    DI_400 as DI,
                                    Adi_400 as Adi,
                                    Reboque_400 as Reboque,
                                    Vol_400 as Vol,
                                    NFRef_400 as NFRef,
                                    Dup_400 as Dup,
                                    Pag_400 as Pag,
                                    Rastro_400 as Rastro
                                    )

except ImportError:
    from pysped.nfe.leiaute import (ProcNFe_310 as ProcNFe,
                                    NFe_310 as NFe,
                                    NFCe_310 as NFCe,
                                    Det_310 as Det,
                                    DI_310 as DI,
                                    Adi_310 as Adi,
                                    Reboque_310 as Reboque,
                                    Vol_310 as Vol,
                                    NFRef_310 as NFRef,
                                    Dup_310 as Dup
                                    )

except (IOError) as err:
    _logger.debug(err)


ClasseProcNFe = ProcNFe
#
# Cabeçalho
#
ClasseNFe = NFe
ClasseNFCe = NFCe

#
# Itens
#
ClasseDet = Det

try:
    ClasseRastro = Rastro_400
except Exception as err:
    ClasseRastro = False
    _logger.debug(err)

ClasseDI = DI
ClasseAdi = Adi

#
# Transporte
#
ClasseReboque = Reboque
ClasseVol = Vol

#
# Documentos referenciados
#
ClasseNFRef = NFRef

#
# Parcelamento e pagamento
#
ClasseDup = Dup

try:
    ClassePag = Pag_400
except Exception as err:
    ClassePag = False
    _logger.debug(err)
