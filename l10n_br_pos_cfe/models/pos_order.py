# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from satcomum.ersat import ChaveCFeSAT

from odoo import api, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_CFE


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)

        document_key = ui_order.get("document_key")
        document_type = ui_order.get("document_type")

        if document_key and document_type == MODELO_FISCAL_CFE:
            key = ChaveCFeSAT(document_key)
            order_fields.update(
                {
                    "document_number": key.numero_cupom_fiscal,
                    "document_serie": key.numero_serie,
                }
            )

        return order_fields
