# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    nfse_nacional_operation_indicator = fields.Selection(
        selection=[
            ("0", "Taxable operation"),
            ("1", "Exempt or non-taxable operation"),
            ("2", "Operation with suspended enforceability"),
            ("3", "Service export"),
        ],
        string="NFS-e Nacional Operation Indicator",
        help="Operation indicator specific to NFS-e Nacional (SEFIN standard).",
    )

    nfse_nacional_tax_regime_code = fields.Char(
        string="NFS-e Nacional Tax Regime Code",
        help="Tax regime code specific to the SEFIN national standard.",
    )
