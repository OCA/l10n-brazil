# Copyright (C) 2023  Felipe Zago Rodrigues - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class DocumentImportWizard(models.TransientModel):
    """
    DocumentImportWizard is defined here so l10n_br_account can be hooked
    with it without depending on l10n_br_fiscal_edi where the actual
    implementation lies.
    """

    _name = "l10n_br_fiscal.document.import.wizard"
    _description = "Import Document Wizard"
    _inherit = "l10n_br_fiscal.base.wizard.mixin"
