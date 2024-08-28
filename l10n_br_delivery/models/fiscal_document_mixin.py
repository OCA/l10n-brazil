# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FiscalDocumentMixin(models.AbstractModel):
    _inherit = "l10n_br_fiscal.document.mixin.fields"

    def _get_default_incoterm(self):
        return self.env.company.incoterm_id

    # Esta sendo implementado aqui para existir nos objetos herdados
    incoterm_id = fields.Many2one(
        comodel_name="account.incoterms",
        string="Incoterm",
        help="International Commercial Terms are a series of"
        " predefined commercial terms used in international"
        " transactions.",
    )

    # proxy fields to enable writing the related (shadowed) fields
    # to the fiscal doc line from the aml through the _inherits system
    # despite they have the same names.
    fiscal_proxy_incoterm_id = fields.Many2one(
        string="Fiscal Proxy Incoterm", related="incoterm_id"
    )

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Carrier",
        ondelete="restrict",
    )
