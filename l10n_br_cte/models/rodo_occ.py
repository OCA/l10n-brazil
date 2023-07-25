# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class Occ(spec_models.SpecModel):
    _name = "l10n_br_cte.occ"
    _inherit = ["cte.40.occ"]

    cte40_occ_rodo_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.rodo", ondelete="cascade"
    )

    cte40_serie = fields.Char(related="serie")

    serie = fields.Char(string="Série da OCC")

    cte40_nOcc = fields.Char(related="nOcc")

    nOcc = fields.Char(string="Número da Ordem de coleta")

    cte40_dEmi = fields.Date(related="dEmi")

    dEmi = fields.Date(
        string="Data de emissão da ordem de coleta",
        help="Data de emissão da ordem de coleta\nFormato AAAA-MM-DD",
    )

    cte40_emiOcc = fields.Many2one(comodel_name="res.partner", string="emiOcc")

    def export_data(self):
        return {
            "cte40_serie": self.cte40_serie,
            "cte40_nOcc": self.cte40_nOcc,
            "cte40_dEmi": self.cte40_dEmi,
            "cte40_emiOcc": {
                "cte40_CNPJ": self.cte40_emiOcc.cte40_serie,
                "cte40_IE": self.cte40_emiOcc.cte40_IE,
                "cte40_UF": self.cte40_emiOcc.cte40_UF,
            },
        }
