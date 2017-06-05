# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError

from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL_EMISSAO_PRODUTO,
    MODELO_FISCAL_EMISSAO_SERVICO,
)
from odoo.addons.sped_imposto.models.sped_calculo_imposto import (
    SpedCalculoImposto
)


class SaleOrder(SpedCalculoImposto, models.Model):
    _inherit = 'sale.order'

    order_line_brazil_ids = fields.One2many(
        comodel_name='sale.order.line.brazil',
        inverse_name='order_id',
        string='Linhas da Fatura',
    )
