# Copyright (C) 2022  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    NCM_FOR_SERVICE_REF,
    PRODUCT_FISCAL_TYPE_SERVICE,
    TAX_DOMAIN_ISSQN,
)


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_deposit_product(self):
        result = super()._prepare_deposit_product()

        fiscal_genre = self.env["l10n_br_fiscal.product.genre"].search(
            [("code", "=", self.env.ref(NCM_FOR_SERVICE_REF).code[0:2])]
        )

        result.update(
            {
                "fiscal_type": PRODUCT_FISCAL_TYPE_SERVICE,
                "tax_icms_or_issqn": TAX_DOMAIN_ISSQN,
                "ncm_id": self.env.ref(NCM_FOR_SERVICE_REF).id,
                "fiscal_genre_id": fiscal_genre.id,
            }
        )
        return result
