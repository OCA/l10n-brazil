# -*- coding: utf-8 -*-
# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class ContractContract(models.Model):

    _inherit = 'contract.contract'

    @api.model
    def _finalize_and_create_invoices(self, invoices_values):
        for invoice in invoices_values:
            invoice['fiscal_document_id'] = False
        return super()._finalize_and_create_invoices(invoices_values)
