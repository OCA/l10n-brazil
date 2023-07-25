# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class Rodoviario(spec_models.SpecModel):
    _name = "l10n_br_cte.rodoviario"
    _inherit = ["cte.40.rodo"]

    document_id = fields.One2many(
        comodel_name="l10n_br_fiscal.document", inverse_name="cte40_rodoviario"
    )

    cte40_RNTRC = fields.Char(
        string="RNTRC",
        store=True,
        related="document_id.cte40_emit.partner_id.rntrc_code",
        help="Registro Nacional de Transportadores Rodoviários de Carga",
    )

    cte40_occ = fields.One2many(
        comodel_name="l10n_br_cte.occ",
        inverse_name="cte40_occ_rodo_id",
        string="Ordens de Coleta associados",
    )

    def export_data(self):
        return {
            "cte40_RNTRC": self.cte40_RNTRC,
            "cte40_occ": self.cte40_occ,
        }
