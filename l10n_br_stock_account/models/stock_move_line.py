# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _put_in_pack(self, package_id=False, package_type_id=False, package_name=False):
        # Since 19.0 packing goes through stock.move.line instead of
        # stock.picking._put_in_pack
        package = super()._put_in_pack(
            package_id=package_id,
            package_type_id=package_type_id,
            package_name=package_name,
        )
        if package:
            for picking in self.picking_id.filtered(
                lambda p: p.picking_type_id.pre_generate_fiscal_document_number
                == "pack"
            ):
                picking._generate_document_number()
        return package
