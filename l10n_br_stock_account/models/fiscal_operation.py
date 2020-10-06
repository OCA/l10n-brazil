# Copyright (C) 2020  Gabriel Cardoso de Faria - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class Operation(models.Model):
    _name = 'l10n_br_fiscal.operation'
    _inherit = [_name, 'stock.invoice.state.mixin']
