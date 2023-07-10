# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base.misc import punctuation_rm
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class ResPartner(spec_models.SpecModel):

    _name = "res.partner"
    _inherit = [
        "res.partner",
        "cte.40.tendereco",
        "cte.40.tlocal",
        "cte.40.tendeemi",
        "cte.40.tcte_dest",
        "cte.40.tresptec",
        "cte.40.tcte_autxml",
    ]
    _cte_search_keys = ["cte40_CNPJ", "cte40_CPF", "cte40_xNome"]

    cte40_CNPJ = fields.Char(
        compute="_compute_cte_data",
        inverse="_inverse_cte40_CNPJ",
        store=True,
    )

    cte40_CPF = fields.Char(
        compute="_compute_cte_data",
        inverse="_inverse_cte40_CPF",
        store=True,
    )

    @api.depends("company_type", "inscr_est", "cnpj_cpf", "country_id")
    def _compute_cte_data(self):
        for rec in self:
            cnpj_cpf = punctuation_rm(rec.cnpj_cpf)
            if cnpj_cpf:
                if rec.is_company:
                    rec.cte40_CNPJ = cnpj_cpf
                    rec.cte40_CPF = None
                else:
                    rec.cte40_CNPJ = None
                    rec.cte40_CPF = cnpj_cpf
