# Copyright (C) 2026-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_information(self):
        """
        Contains details about how to initialize a payment method
        with the code x.
        The contained info are:
            mode: Either unique if we only want one of them at a single time
                (payment providers for example) or multi if we want the
                method on each journal fitting the domain.
            domain: The domain defining the eligible journals.
            currency_id: The id of the currency necessary on the journal
                (or company) for it to be eligible.
            country_id: The id of the country needed on the company
                for it to be eligible.
            hidden: If set to true, the method will not be automatically
                added to the journal, and will not be selectable by the user.
        """
        res = super()._get_payment_method_information()

        res["240"] = {
            "mode": "multi",
            "domain": [("type", "=", "bank")],
            "currency_id": self.env.ref("base.BRL").id,
            "country_id": self.env.ref("base.br").id,
        }

        res["400"] = {
            "mode": "multi",
            "domain": [("type", "=", "bank")],
            "currency_id": self.env.ref("base.BRL").id,
            "country_id": self.env.ref("base.br").id,
        }

        res["500"] = {
            "mode": "multi",
            "domain": [("type", "=", "bank")],
            "currency_id": self.env.ref("base.BRL").id,
            "country_id": self.env.ref("base.br").id,
        }

        return res
