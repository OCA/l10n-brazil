# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class DuimpTaxWarningWizard(models.TransientModel):
    """Last check before generating the vendor bill when some rate of the
    DUIMP has no l10n_br_fiscal.tax registered.

    The amounts are not lost - they stay on the invoice line - but they
    post to no tax account, so the bill books them as part of the expense.
    Generating anyway is a legitimate choice (the tax can be registered
    and the DUIMP re-imported later), hence a confirmation and not a
    blocking error.
    """

    _name = "l10n_br_duimp.tax_warning_wizard"
    _description = "DUIMP Missing Tax Confirmation"

    declaration_id = fields.Many2one(
        comodel_name="l10n_br_duimp.declaration",
        required=True,
        ondelete="cascade",
    )

    message = fields.Text(readonly=True)

    def action_confirm(self):
        self.ensure_one()
        return self.declaration_id.with_context(
            duimp_skip_tax_check=True
        ).action_generate_vendor_bill()
