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

    fiscal_incoterm_id = fields.Many2one(related="incoterm_id")

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Carrier",
        ondelete="restrict",
    )

    expected_date = fields.Datetime(
        string="Expected Date",
        help="Expected date for the goods to be delivered to the recipient.",
    )

    # Remetente
    partner_sendering_id = fields.Many2one(
        "res.partner",
        string="Sender",
        help="Responsible for sending the goods, usually the issuer of the NFe.",
    )

    # Expedidor
    partner_shippering_id = fields.Many2one(
        "res.partner",
        string="Shipper",
        help="The one responsible for delivering the cargo to the carrier when \
            the shipment is not carried out by the sender.",
    )

    # # Destinatário
    # partner_shipping_id = fields.Many2one(
    #     "res.partner",
    #     string="Recipient",
    #     help="The one who receives the goods at the end of the transport \
    #         route, can be an individual or a company.",
    # )

    # Recebedor
    partner_receivering_id = fields.Many2one(
        "res.partner",
        string="Receiver",
        help="Actor who receives the goods. He is considered an intermediary \
            between the issuer and the final recipient.",
    )
