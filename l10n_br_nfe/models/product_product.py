# Copyright 2020 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.osv import expression

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    CFOP_TYPE_MOVE_2_PRODUCT_FISCAL_TYPE,
)


class ProductProduct(models.Model):
    _inherit = "product.product"
    _nfe40_odoo_module = "odoo.addons.l10n_br_nfe_spec.models.v4_0.leiaute_nfe_v4_00"
    _nfe_search_keys = ["default_code", "barcode"]

    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        domain_name, domain_barcode, domain_default_code = [], [], []

        if parent_dict.get("nfe40_xProd") and parent_dict.get("nfe40_cProd"):
            supplier_id = self.env["product.supplierinfo"].search(
                [
                    ("product_code", "=", parent_dict["nfe40_cProd"]),
                    ("product_name", "=", parent_dict["nfe40_xProd"]),
                ],
                limit=1,
            )
            if supplier_id and supplier_id.product_id:
                return supplier_id.product_id.id
        if parent_dict.get("nfe40_xProd"):
            rec_dict["name"] = parent_dict["nfe40_xProd"]
            domain_name = [("name", "=", rec_dict.get("name"))]

        if (
            parent_dict.get("nfe40_cEANTrib")
            and parent_dict["nfe40_cEANTrib"] != "SEM GTIN"
        ):
            rec_dict["barcode"] = parent_dict["nfe40_cEANTrib"]
            domain_barcode = [("barcode", "=", rec_dict.get("barcode"))]

        if parent_dict.get("nfe40_cProd"):
            rec_dict["default_code"] = parent_dict["nfe40_cProd"]
            domain_default_code = [("default_code", "=", rec_dict.get("default_code"))]

        domain = expression.OR([domain_name, domain_barcode, domain_default_code])
        match = self.search(domain, limit=1)
        if match:
            return match.id

        if self._context.get("dont_create_product_product"):
            return False

        if self._context.get("dry_run"):
            rec_id = self.new(rec_dict).id
        else:
            rec_id = self.with_context(parent_dict=parent_dict).create(rec_dict).id

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
            values["fiscal_genre_id"] = (
                self.env["l10n_br_fiscal.product.genre"]
                .search([("code", "=", parent_dict["nfe40_NCM"][:2])], limit=1)
                .id
            )

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
            values["fiscal_type"] = self._map_fiscal_type_from_context()
        return values

    def _map_fiscal_type_from_context(self):
        """
        Automatically determines the product's fiscal type based on the
        imported invoice context.

        :param env: Odoo environment containing the execution context.
        :return: Product fiscal type or False if it cannot be determined.
        """
        fiscal_type = False
        parent_dict = self.env.context.get("parent_dict")

        if parent_dict:
            # Mapping based on CFOP
            cfop_tuple = parent_dict.get("cfop_inverse_id")
            if cfop_tuple and isinstance(cfop_tuple, tuple):
                cfop = cfop_tuple[0]
                cfop_id = self.env["l10n_br_fiscal.cfop"].browse(cfop)
                fiscal_type = CFOP_TYPE_MOVE_2_PRODUCT_FISCAL_TYPE.get(
                    cfop_id.type_move
                )

            # If a fiscal operation line exists, overwrite the previous value
            fol_tuple = parent_dict.get("fiscal_operation_line_id")
            if fol_tuple and isinstance(fol_tuple, tuple):
                fol_id = fol_tuple[0]
                fiscal_operation_line_id = self.env[
                    "l10n_br_fiscal.operation.line"
                ].browse(fol_id)
                if fiscal_operation_line_id.product_type:
                    fiscal_type = fiscal_operation_line_id.product_type

        return fiscal_type
