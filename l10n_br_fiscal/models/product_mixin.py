# Copyright (C) 2021  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models

from ..constants.fiscal import (
    NCM_FOR_SERVICE_REF,
    PRODUCT_FISCAL_TYPE_SERVICE,
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ISSQN,
)


class ProductMixin(models.AbstractModel):
    _name = "l10n_br_fiscal.product.mixin"
    _description = "Fiscal Product Mixin"

    @api.depends("fiscal_type", "fiscal_genre_id")
    def _compute_ncm_id(self):
        for product in self:
            if product.fiscal_type == PRODUCT_FISCAL_TYPE_SERVICE:
                product.ncm_id = self.env.ref(NCM_FOR_SERVICE_REF)
            elif product.fiscal_genre_id and product.ncm_id:
                if product.fiscal_genre_id.code != product.ncm_id.code[0:2]:
                    product.ncm_id = False
            elif product.ncm_id is None:
                product.ncm_id = False

    @api.depends("ncm_id")
    def _compute_fiscal_genre_id(self):
        for product in self:
            if product.ncm_id:
                product.fiscal_genre_id = self.env[
                    "l10n_br_fiscal.product.genre"
                ].search([("code", "=", product.ncm_id.code[0:2])])
            elif product.fiscal_genre_id is None:
                product.fiscal_genere_id = False

    @api.depends("fiscal_type")
    def _compute_tax_icms_or_issqn(self):
        for product in self:
            if product.fiscal_type == PRODUCT_FISCAL_TYPE_SERVICE:
                product.tax_icms_or_issqn = TAX_DOMAIN_ISSQN
            else:
                product.tax_icms_or_issqn = TAX_DOMAIN_ICMS
