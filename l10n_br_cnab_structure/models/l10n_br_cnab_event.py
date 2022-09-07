# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models, api


class CNABReturnEvent(models.Model):

    _inherit = "l10n_br_cnab.return.event"

    @api.model
    def create(self, vals):
        """
        When for cnab outbound payment processed by this module the
        bank_payment_line_id is filled based on your_number field
        """
        event = super().create(vals)
        if not event.cnab_return_log_id.cnab_structure_id:
            # if there is no cnab_structure_id it is because the return file is not being
            # processed by this module, so there is nothing to do here.
            return event
        if event.cnab_return_log_id.type == "outbound":
            bank_payment_line_id = self.env["bank.payment.line"].search(
                [("name", "=", event.your_number)]
            )
            event.bank_payment_line_id = bank_payment_line_id

        # TODO:
        # quando for cobrança temos que mapear o bank line pelo campo nosso numero e
        # também pelo journal do banco. porém o bank line não tem journal, mapear depois.
        # if  event.cnab_return_log_id.type == "inbound":
        #     bank_payment_line_id = self.env["bank.payment.line"].search(
        #         [("name", "=", event.own_numner)]
        #     )
        #     event.bank_payment_line_id = bank_payment_line_id
        return event
