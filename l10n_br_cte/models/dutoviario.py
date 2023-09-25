# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class Dutoviario(spec_models.SpecModel):
    _name = "l10n_br_cte.modal.dutoviario"
    _inherit = "cte.40.duto"

    cte40_dIni = fields.Date(string="Data de Início da prestação do serviço")

    cte40_dFim = fields.Date(string="Data de Fim da prestação do serviço")

    cte40_vTar = fields.Float(string="Valor da tarifa")
