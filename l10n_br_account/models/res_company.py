# 2024 Copyright (C) Akretion (<http://www.akretion.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = "res.company"

    def write(self, values):
        """
        Overriden so we can change the currency_id of base.main_company
        and specific demo companies even if constraints would normally prevent it.
        """
        try:
            return super().write(values)
        except UserError as e:
            brl_currency = self.env.ref("base.BRL", raise_if_not_found=False)
            usd_currency = self.env.ref("base.USD", raise_if_not_found=False)
            if (
                not brl_currency
                or not usd_currency
                or values.get("currency_id") not in (brl_currency.id, usd_currency.id)
            ):
                raise e

            demo_refs = [
                "base.main_company",
                "l10n_br_base.empresa_simples_nacional",
                "l10n_br_base.empresa_lucro_presumido",
            ]

            allowed_companies = self.env["res.company"]
            for ref in demo_refs:
                company = self.env.ref(ref, raise_if_not_found=False)
                if company:
                    allowed_companies |= company

            if allowed_companies and not (self - allowed_companies):
                return models.Model.write(self, values)

            raise e
