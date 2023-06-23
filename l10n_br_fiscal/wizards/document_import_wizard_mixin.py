# Copyright (C) 2023  Felipe Zago Rodrigues - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import FISCAL_IN_OUT_ALL


class DocumentImportWizardMixin(models.TransientModel):

    _name = "l10n_br_fiscal.document.import.wizard.mixin"
    _inherit = "l10n_br_fiscal.base.wizard.mixin"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.user.company_id,
    )

    importing_type = fields.Selection(
        selection=[("xml_file", "XML File")], string="Importing Type", required=True
    )

    xml = fields.Binary(string="XML to Import")

    fiscal_operation_type = fields.Selection(
        string="Fiscal Operation Type", selection=FISCAL_IN_OUT_ALL
    )

    def import_xml(self):
        self.document_id = self.create_edoc_from_xml()

        return {
            "name": _("Document Imported"),
            "type": "ir.actions.act_window",
            "target": "current",
            "views": [[False, "form"]],
            "res_id": self.document_id.id,
            "res_model": "l10n_br_fiscal.document",
        }

    def create_edoc_from_xml(self):
        return NotImplemented
