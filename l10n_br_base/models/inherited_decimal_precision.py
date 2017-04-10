# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import api, fields, models
from pybrasil.valor.decimal import Decimal as D


class DecimalPrecision(models.Model):
    _inherit = 'decimal.precision'

    def write(self, dados):
        res = super(DecimalPrecision, self).write(dados)
        import ipdb; ipdb.set_trace();

        for dp in self:
            #
            # Mantém a sincronia entre as casas decimais dos campos float
            # e monetary
            #
            if dp.id == self.env.ref('sped.CASAS_DECIMAIS_UNITARIO').id:
                simbolo = self.env.ref('sped.SIMBOLO_VALOR_UNITARIO')
                arredondamento = D(10) ** (D(dp.digits or 0) * -1)
                simbolo.rounding = arredondamento

        return res
