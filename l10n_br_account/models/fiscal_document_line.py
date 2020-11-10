# Copyright (C) 2020 - Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class FiscalDocumentLine(models.Model):
    _inherit = 'l10n_br_fiscal.document.line'

    def _get_product_price(self):
        if not self.price_unit or self.price_unit in (
                self.product_id.list_price, self.product_id.standard_price):
            return super()._get_product_price()
        return self.price_unit
