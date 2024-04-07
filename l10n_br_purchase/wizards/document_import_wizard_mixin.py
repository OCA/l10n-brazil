# Copyright 2024 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DocumentImportWizardMixin(models.TransientModel):

    _inherit = "l10n_br_fiscal.document.import.wizard.mixin"

    purchase_id = fields.Many2one(
        comodel_name="purchase.order",
        string="Purchase Order",
    )
