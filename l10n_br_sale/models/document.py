# Copyright 2023 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    # proxy field used to handle partner_shipping_id
    # in l10n_br_fiscal.document while the sale module
    # also brings a partner_shipping_id field to account.move.
    fiscal_proxy_partner_shipping_id = fields.Many2one(
        string="Fiscal Partner Shipping",
        related="partner_shipping_id",
        readonly=False,
    )
