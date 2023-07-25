# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class Dutoviario(spec_models.SpecModel):
    _name = "l10n_br_cte.dutoviario"
    _inherit = ["cte.40.duto"]

    document_id = fields.One2many(
        comodel_name="l10n_br_fiscal.document", inverse_name="cte40_dutoviario"
    )

    cte40_dIni = fields.Date(related="dIni")

    dIni = fields.Date(string="Data de Início da prestação do serviço")

    cte40_dFim = fields.Date(related="dFim")

    dFim = fields.Date(string="Data de Fim da prestação do serviço")

    cte40_vTar = fields.Float(related="vTar")

    vTar = fields.Float(string="Valor da tarifa")

    def export_data(self):
        return {
            "cte40_dIni": self.cte40_dIni,
            "cte40_dFim": self.cte40_dFim,
            "cte40_vTar": self.cte40_vTar,
        }
