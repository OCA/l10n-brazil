# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class NFe(models.Model):

    _inherit = "l10n_br_fiscal.document"

    @api.depends("partner_shipping_id")
    def _compute_entrega_data(self):
        for doc in self:
            if doc.document_type == "65" and doc.partner_id.is_anonymous_consumer:
                doc.nfe40_entrega = None
            else:
                doc.nfe40_entrega = doc.partner_shipping_id

    @api.depends("partner_id")
    def _compute_dest_data(self):
        for doc in self:  # TODO if out
            if doc.document_type == "65":
                if doc.partner_id.is_anonymous_consumer and not doc.partner_id.cnpj_cpf:
                    doc.nfe40_dest = None
                else:
                    doc.nfe40_dest = doc.partner_id
            else:
                doc.nfe40_dest = doc.partner_id
