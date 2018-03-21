# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

import sys
import logging
from mdfelib.v3_00 import mdfe as mdfe3
from mdfelib.v3_00 import mdfeModalRodoviario as rodo3

_logger = logging.getLogger(__name__)

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL_MDFE,
    TIPO_TRANSPORTADOR,
    MODALIDADE_TRANSPORTE,
    TIPO_EMITENTE,
    TIPO_RODADO,
    TIPO_CARROCERIA,
    AMBIENTE_MDFE_PRODUCAO,
    TIPO_EMISSAO_MDFE_NORMAL,
    TIPO_EMISSAO_MDFE_CONTINGENCIA,
)

try:
    from pysped.nfe.webservices_flags import *
    from pysped.nfe.leiaute import *
    from pybrasil.inscricao import limpa_formatacao
    from pybrasil.data import (parse_datetime, UTC, data_hora_horario_brasilia,
                               agora)
    from pybrasil.valor import formata_valor
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumento(models.Model):
    _inherit = 'sped.documento'

    def monta_mdfe(self, processador=None):
        self.ensure_one()
        