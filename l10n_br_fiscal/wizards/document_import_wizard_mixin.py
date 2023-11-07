# Copyright (C) 2023  Felipe Zago Rodrigues - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import FISCAL_IN_OUT_ALL


class DocumentImportWizardMixin(models.TransientModel):
    _name = "l10n_br_fiscal.document.import.wizard.mixin"
    _description = "Wizard Import Document Mixin"
    _inherit = "l10n_br_fiscal.base.wizard.mixin"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company.id,
    )

    importing_type = fields.Selection(
        selection=[("xml_file", "XML File")],
        string="Importing Type",
        required=True,
        default="xml_file",
    )

    xml = fields.Binary(string="XML to Import")

    fiscal_operation_type = fields.Selection(
        string="Fiscal Operation Type", selection=FISCAL_IN_OUT_ALL
    )
