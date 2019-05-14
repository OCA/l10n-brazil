# Copyright (C) 2019 Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class ProductGenre(models.Model):
    _name = 'fiscal.product.genre'
    _inherit = 'fiscal.data.abstract'
    _description = 'Fiscal Product Genre'
