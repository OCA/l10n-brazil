# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
   _logger.debug(err)


class DecimalPrecision(models.Model):
    _inherit = b'decimal.precision'

    @api.multi
    def write(self, dados):
        #
        # Validação do número máximo de casas decimais
        #
        if 'digits' in dados:
            for dp in self:
                if dp.id == \
                    self.env.ref('l10n_br_base.CASAS_DECIMAIS_QUANTIDADE').id:
                    if dados['digits'] > 4:
                        raise ValidationError(
                            'O número máximo de casas decimais para os ' +
                            'campos de quantidade é 4!'
                        )

                elif dp.id == \
                    self.env.ref('l10n_br_base.CASAS_DECIMAIS_UNITARIO').id:
                    if dados['digits'] > 11:
                        raise ValidationError(
                            'O número máximo de casas decimais para os ' +
                            'campos de valor unitário é 11!'
                        )

                elif dp.id == \
                    self.env.ref('l10n_br_base.CASAS_DECIMAIS_PESO').id:
                    if dados['digits'] > 4:
                        raise ValidationError(
                            'O número máximo de casas decimais para os ' +
                            'campos de peso é 4!'
                        )

        res = super(DecimalPrecision, self).write(dados)

        for dp in self:
            #
            # Mantém a sincronia entre as casas decimais dos campos float
            # e monetary
            #
            if dp.id == self.env.ref('l10n_br_base.CASAS_DECIMAIS_UNITARIO').id:
                simbolo = self.env.ref('l10n_br_base.SIMBOLO_VALOR_UNITARIO')
                arredondamento = D(10) ** (D(dp.digits or 0) * -1)
                simbolo.rounding = arredondamento

            elif dp.id == self.env.ref('l10n_br_base.CASAS_DECIMAIS_PESO').id:
                simbolo = self.env.ref('l10n_br_base.SIMBOLO_PESO')
                arredondamento = D(10) ** (D(dp.digits or 0) * -1)
                simbolo.rounding = arredondamento
        return res
