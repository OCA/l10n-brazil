# Copyright (C) 2025  Marcel Savegnago <https://escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class OperationIndicator(models.Model):
    """Operation Indicator

    This model stores the Operation Indicators (cIndOp) table according to
    Annex VII of the NFS-e Nacional technical documentation (v1.03.00, NT 009),
    part of the Brazilian Tax Reform (Reforma Tributária do Consumo).

    The cIndOp field is used in the Service Provision Declaration (DPS)
    to categorize consumption operations, as required by Art. 11 of
    Complementary Law No. 214/2025.

    This table will become mandatory from January 1, 2026.
    """

    _name = "l10n_br_fiscal.operation.indicator"
    _inherit = "l10n_br_fiscal.data.abstract"
    _description = "Operation Indicator"
    _order = "code"

    code = fields.Char(
        string="Operation Indicator Code",
        required=True,
        index=True,
        size=6,
        help="Operation indicator code according to Annex VII of the NFS-e "
        "(e.g., 020101, 030101)",
    )

    operation_type = fields.Text(
        required=True,
        help="Type of operation according to Art. 11 of Complementary Law No. 214/2025",
    )

    operation_location = fields.Text(
        string="Operation Location Consideration",
        help="Where the operation is considered to take place according to "
        "the legislation",
    )

    supply_characteristic = fields.Text(
        help="Specific characteristic of the supply execution that determines "
        "the place of supply",
    )

    supply_location = fields.Text(
        string="DFe Supply Location",
        required=True,
        help="Place of supply to be identified in the Digital Fiscal Document "
        "(DFe), such as supplier establishment, acquirer address, "
        "recipient address, or other locations depending on the operation",
    )

    legal_basis = fields.Char(
        help="Provision of Complementary Law No. 214/2025 that defines the place "
        "of the operation",
    )

    note = fields.Text()

    nfse_incidence_location = fields.Char(
        string="NFS-e IBS Incidence Location",
        help="Where the IBS is due in the NFS-e for this indicator",
    )

    document_type_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.document.type",
        relation="operation_indicator_document_type_rel",
        string="Related DFes",
        help="Digital Fiscal Documents that accept this indicator",
    )
