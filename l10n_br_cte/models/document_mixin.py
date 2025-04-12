# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DocumentMixin(models.AbstractModel):
    _inherit = "l10n_br_fiscal.document.mixin"

    # Sender (Remetente)
    partner_sendering_id = fields.Many2one(
        "res.partner",
        string="Sender Address",
        help="The partner responsible for sending the goods, typically the issuer of "
        "the document. This field is primarily used when issuing the CT-e.",
    )

    # Shipper (Expedidor)
    partner_shippering_id = fields.Many2one(
        "res.partner",
        string="Shipper Address",
        help="The partner responsible for delivering the cargo to the carrier, if not "
        "done directly by the sender. This field is primarily used when issuing "
        "the CT-e.",
    )

    # Receiver (Recebedor)
    partner_receivering_id = fields.Many2one(
        "res.partner",
        string="Receiver Address",
        help="The intermediary partner who receives the goods before they reach the "
        "final recipient, often involved in verification, temporary storage, or "
        "further distribution. This field is primarily used when issuing the "
        "CT-e.",
    )

    partner_insurance_id = fields.Many2one(
        "res.partner",
        string="Insurance Provider",
        help="The partner providing insurance coverage for the transported goods. "
        "This field is primarily used when issuing the CT-e.",
    )

    insurance_policy = fields.Char(
        help="The insurance policy number covering the transported goods. "
        "This field is primarily used when issuing the CT-e.",
    )

    insurance_endorsement = fields.Char(
        help="The endorsement number associated with the insurance policy, indicating "
        "any modifications or adjustments to the coverage. This field is "
        "primarily used when issuing the CT-e.",
    )
