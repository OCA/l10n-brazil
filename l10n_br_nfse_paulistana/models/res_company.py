# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    provedor_nfse = fields.Selection(
        selection_add=[
            ("paulistana", "Paulistana"),
        ]
    )

    nfse_paulistana_schema = fields.Selection(
        selection=[
            ("v02", "Legacy - Version 1 (taxable event until 2025-12-31)"),
            ("v03", "Tax Reform - Version 2 (IBS/CBS)"),
        ],
        string="Paulistana NFS-e Schema",
        default="v02",
        help=(
            "Schema version used to issue/transmit the Paulistana NFS-e.\n"
            "- Legacy (Version 1): layout until 2025-12-31 (nfselib v02 "
            "bindings).\n"
            "- Tax Reform (Version 2): layout with IBS/CBS (nfselib v03 "
            "bindings)."
        ),
    )
