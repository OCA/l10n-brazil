# Copyright (C) 2020  Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# Copyright (C) 2021  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def _get_price_unit_invoice(self, inv_type, partner, qty=1):
        result = super()._get_price_unit_invoice(inv_type, partner, qty)
        # Caso tenha Sale Line já vem desagrupado aqui devido ao KEY
        if len(self) == 1:
            # Caso venha apenas uma linha porem sem
            # sale_line_id é preciso ignora-la
            if self.sale_line_id and self.sale_line_id.price_unit != result:
                result = self.sale_line_id.price_unit

        return result

    def _get_new_picking_values(self):
        # IMPORTANTE: a sequencia de update dos dicionarios quando o
        # partner_shipping_id é diferente, o metodo do fiscal está
        # sobre escrevendo o partner_id e acaba criando um picking
        # sem o partner_id caso esse dict atualize o do super
        values = {}
        if self.sale_line_id:
            values = \
                self.sale_line_id.order_id._prepare_br_fiscal_dict()

        values.update(super()._get_new_picking_values())
        # TODO - remover o pop abaixo depois do merge
        #  https://github.com/OCA/l10n-brazil/pull/1099
        #  , não é necessário
        # Remover o dummy
        values.pop('fiscal_document_id')
        return values
