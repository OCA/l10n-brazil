# Copyright 2020 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.osv import expression


class ProductProduct(models.Model):
    _inherit = "product.product"
    _nfe_search_keys = ["default_code", "barcode"]

    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        create_dict = {}
        domain_name, domain_barcode = [], []
        if parent_dict.get("nfe40_xProd"):
            rec_dict["name"] = parent_dict["nfe40_xProd"]
            domain_name = [("name", "=", rec_dict.get("name"))]
            create_dict.update(
                {
                    "name": rec_dict["name"],
                }
            )
        if (
            parent_dict.get("nfe40_cEANTrib")
            and parent_dict["nfe40_cEANTrib"] != "SEM GTIN"
        ):
            rec_dict["barcode"] = parent_dict["nfe40_cEANTrib"]
            domain_barcode = [("barcode", "=", rec_dict.get("barcode"))]
            create_dict.update({"barcode": rec_dict["barcode"]})
        domain = expression.OR([domain_name, domain_barcode])
        match = self.search(domain, limit=1)
        if match:
            return match.id
        if self._context.get("dry_run"):
            rec_id = self.new(create_dict).id
        else:
            rec_id = self.with_context(parent_dict=parent_dict).create(create_dict).id
        return rec_id

    @api.model
    def default_get(self, default_fields):
        """
        The nfe.40.prod mixin (prod XML tag) cannot be injected in
        the product.product object because the tag includes attributes from the
        Odoo fiscal document line and because we may have an Nfe with
        lines decsriptions instead of full blown products.
        So a part of the mapping is done
        in the fiscal document line:
        from Odoo -> XML by using related fields/_compute
        from XML -> Odoo by overriding the product default_get method
        """
        values = super().default_get(default_fields)
        parent_dict = self._context.get("parent_dict", {})
        if parent_dict.get("nfe40_xProd"):
            values["name"] = parent_dict["nfe40_xProd"]

        # Price Unit
        if parent_dict.get("nfe40_vUnCom"):
            values["standard_price"] = parent_dict.get("nfe40_vUnCom")
            values["list_price"] = parent_dict.get("nfe40_vUnCom")

        # Barcode
        if (
            parent_dict.get("nfe40_cEANTrib")
            and parent_dict["nfe40_cEANTrib"] != "SEM GTIN"
        ):
            values["barcode"] = parent_dict["nfe40_cEANTrib"]

        # NCM
        if parent_dict.get("nfe40_NCM"):
            ncm = self.env["l10n_br_fiscal.ncm"].search(
                [("code_unmasked", "=", parent_dict["nfe40_NCM"])], limit=1
            )

            values["ncm_id"] = ncm.id

            if not ncm:  # FIXME should not happen with prod data
                ncm = (
                    self.env["l10n_br_fiscal.ncm"]
                    .sudo()
                    .create(
                        {
                            "name": parent_dict["nfe40_NCM"],
                            "code": parent_dict["nfe40_NCM"],
                        }
                    )
                )
                values["ncm_id"] = ncm.id
        return values
