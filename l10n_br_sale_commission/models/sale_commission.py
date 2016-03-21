# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class Commission(models.Model):
    _inherit = 'sale.commission'

    amount_base_type = fields.Selection(selection_add=[("notax",
                                                       "Valor venda s/ impostos")])