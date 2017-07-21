# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class BankPaymentLine(models.Model):

    _inherit = 'bank.payment.line'

    @api.model
    def same_fields_payment_line_and_bank_payment_line(self):
        """
        This list of fields is used both to compute the grouping
        hashcode and to copy the values from payment line
        to bank payment line
        The fields must have the same name on the 2 objects
        """
        same_fields = super(
            BankPaymentLine, self
        ).same_fields_payment_line_and_bank_payment_line()

        # TODO: Implementar campo brasileiros que permitem mesclar linhas

        # same_fields = [
        #     'currency', 'partner_id',
        #     'bank_id', 'date', 'state']

        return same_fields
