# Copyright (C) 2022  Renan Hiroki Bastos - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models

# from datetime import datetime


class NfeImport(models.TransientModel):
    """Importar XML Nota Fiscal Eletrônica"""

    _inherit = "l10n_br_nfe.import_xml"

    # TODO: Mover isso pro módulo l10n_br_nfe
    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Fiscal Operation",
    )

    def _create_edoc_from_xml(self):
        edoc = super(
            NfeImport, self.with_context(create_from_document=True)
        )._create_edoc_from_xml()
        edoc.fiscal_operation_id = self.fiscal_operation_id

        return edoc
