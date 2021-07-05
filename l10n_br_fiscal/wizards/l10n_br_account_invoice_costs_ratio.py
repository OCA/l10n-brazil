#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Daniel Sadamo <sadamo@kmee.com.br>
#    @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from odoo.addons.l10n_br_base.tools.misc import calc_price_ratio


class L10nBrAccountProductInvoiceCostsRatio(models.TransientModel):

    _name = "l10n_br_account_product.invoice.costs_ratio"
    _description = "Ratio costs on invoice"

    amount_freight_value = fields.Float("Frete")
    amount_insurance_value = fields.Float("Seguro")
    amount_other_value = fields.Float("Outros Custos")

    def set_invoice_costs_ratio(self):

        if not self._context.get("active_model") in "account.invoice":
            return False
        for delivery in self:
            for invoice in self.env["account.invoice"].browse(
                self._context.get("active_ids", [])
            ):
                for line in invoice.invoice_line_ids:
                    vals = {
                        "freight_value": calc_price_ratio(
                            line.price_gross,
                            delivery.amount_freight_value,
                            invoice.amount_price_gross,
                        ),
                        "insurance_value": calc_price_ratio(
                            line.price_gross,
                            delivery.amount_insurance_value,
                            invoice.amount_price_gross,
                        ),
                        "other_value": calc_price_ratio(
                            line.price_gross,
                            delivery.amount_other_value,
                            invoice.amount_price_gross,
                        ),
                    }
                    line.write(vals)
                invoice._compute_amount()
        return True
