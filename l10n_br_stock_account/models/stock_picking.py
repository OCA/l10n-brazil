# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = [_name, 'l10n_br_fiscal.document.mixin']
