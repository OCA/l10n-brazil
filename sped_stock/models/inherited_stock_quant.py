# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    #
    # Isto desativa a criação de lançamento contábil pelo estoque, o que
    # permite que a gente faça os ajustes pra controlar o custo médio do
    # estoque pelos documentos fiscais, e não pela contabilidade, que nem
    # todo mundo vai ter instalado, e se tiver, pra funcionar certo, não
    # vai ser a padrão do Odoo
    #
    def _account_entry_move(self, move):
        return False
