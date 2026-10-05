# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DfeDistributionLog(models.Model):
    _inherit = "l10n_br_fiscal_dfe.distribution_log"

    fiscal_type = fields.Selection(
        selection_add=[("nfse", "NFS-e")],
        ondelete={"nfse": "cascade"},
    )
