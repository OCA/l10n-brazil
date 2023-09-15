# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class ProductProduct(spec_models.SpecModel):
    _name = "product.product"
    _inherit = [
        "product.product",
        "mdfe.30.prodpred",
    ]

    mdfe30_xProd = fields.Char(related="name")

    mdfe30_cEAN = fields.Char(related="barcode")

    mdfe30_NCM = fields.Char(string="ncm_id.code")

    mdfe30_tpCarga = fields.Selection(default="05")
