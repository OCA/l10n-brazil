# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    PRODUCT_FISCAL_TYPE_SERVICE,
    TAX_DOMAIN_ISSQN,
)

# NFS-e Nacional: "sem incidencia de ISSQN e ICMS", used for the rental of
# movable goods until 99.04.01 (Locacao de Bens Moveis) is in production
NATIONAL_TAXATION_CODE_RENTAL = "99.01.01"


class CreateRentalProduct(models.TransientModel):
    _inherit = "create.rental.product"

    @api.model
    def _prepare_rental_product(self):
        values = super()._prepare_rental_product()
        # rental of movable goods is not a goods operation: without the ISSQN
        # domain the fiscal mapping applies ICMS/IPI from the company
        values["fiscal_type"] = PRODUCT_FISCAL_TYPE_SERVICE
        values["tax_icms_or_issqn"] = TAX_DOMAIN_ISSQN
        code = self.env["l10n_br_fiscal.national.taxation.code"].search(
            [("code", "in", (NATIONAL_TAXATION_CODE_RENTAL, "990101"))], limit=1
        )
        if code:
            values["national_taxation_code_id"] = code.id
        return values
