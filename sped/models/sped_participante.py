# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.l10n_br_base.constante_tributaria import (
    INDICADOR_IE_DESTINATARIO,
    INDICADOR_IE_DESTINATARIO_ISENTO,
    INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE,
    REGIME_TRIBUTARIO,
    REGIME_TRIBUTARIO_LUCRO_PRESUMIDO,
    REGIME_TRIBUTARIO_LUCRO_REAL,
    REGIME_TRIBUTARIO_SIMPLES,
    REGIME_TRIBUTARIO_SIMPLES_EXCESSO,
    TIPO_PESSOA_JURIDICA,
)

_logger = logging.getLogger(__name__)

#try:
if True:
    from email_validator import validate_email

    from pybrasil.base import mascara, primeira_maiuscula
    from pybrasil.inscricao import (formata_cnpj, formata_cpf,
                                    limpa_formatacao,
                                    formata_inscricao_estadual, valida_cnpj,
                                    valida_cpf, valida_inscricao_estadual)
    from pybrasil.telefone import (formata_fone, valida_fone_fixo,
                                   valida_fone_celular,
                                   valida_fone_internacional)

#except (ImportError, IOError) as err:
#    _logger.debug(err)


class Participante(models.Model):
    _inherit = 'sped.participante'

    @api.onchange('regime_tributario')
    def onchange_regime_tributario(self):
        res = {}
        valores = {}
        res['value'] = valores

        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            valores['al_pis_cofins_id'] = self.env.ref(
                'sped.ALIQUOTA_PIS_COFINS_SIMPLES').id

        elif self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES_EXCESSO:
            valores['al_pis_cofins_id'] = self.env.ref(
                'sped.ALIQUOTA_PIS_COFINS_LUCRO_PRESUMIDO').id

        elif self.regime_tributario == REGIME_TRIBUTARIO_LUCRO_PRESUMIDO:
            valores['al_pis_cofins_id'] = self.env.ref(
                'sped.ALIQUOTA_PIS_COFINS_LUCRO_PRESUMIDO').id

        elif self.regime_tributario == REGIME_TRIBUTARIO_LUCRO_REAL:
            valores['al_pis_cofins_id'] = self.env.ref(
                'sped.ALIQUOTA_PIS_COFINS_LUCRO_REAL').id

        return res
