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
        # inverse="_inverse_cte40_CNPJ",
        store=True,
    )

    cte40_CPF = fields.Char(
        compute="_compute_cte_data",
        inverse="_inverse_cte40_CPF",
        store=True,
    )

    # enderToma/enderEmit/enderReme/enderEmit
    cte40_xLgr = fields.Char(related="street_name", readonly=True)
    cte40_nro = fields.Char(related="street_number", readonly=True)
    cte40_xCpl = fields.Char(related="street2", readonly=True)
    cte40_xBairro = fields.Char(related="district", readonly=True)
    cte40_cMun = fields.Char(related="city_id.ibge_code", readonly=True)
    cte40_xMun = fields.Char(related="city_id.name", readonly=True)
    cte40_UF = fields.Char(related="state_id.code")
    cte40_CEP = fields.Char(
        compute="_compute_nfe_data", inverse="_inverse_nfe40_CEP", compute_sudo=True
    )
    cte40_cPais = fields.Char(related="country_id.bc_code")
    cte40_xPais = fields.Char(related="country_id.name")

    nfe40_xNome = fields.Char(related="legal_name")

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

    def _inverse_cte40_CNPJ(self):
        for rec in self:
            if rec.cte40_CNPJ:
                rec.is_company = True
                rec.cte40_choice2 = "cte40_CPF"
                rec.cte40_choice6 = "cte40_CPF"
                if rec.country_id.code != "BR":
                    rec.cte40_choice7 = "cte40_idEstrangeiro"
                else:
                    rec.cte40_choice7 = "cte40_CNPJ"
                rec.cte40_choice7 = "cte40_CPF"
                rec.cte40_choice8 = "cte40_CPF"
                rec.cte40_choice19 = "cte40_CPF"
                rec.cnpj_cpf = cnpj_cpf.formata(str(rec.cte40_CNPJ))

    def _inverse_cte40_CPF(self):
        for rec in self:
            if rec.cte40_CPF:
                rec.is_company = False
                rec.cte40_choice2 = "cte40_CNPJ"
                rec.cte40_choice6 = "cte40_CNPJ"
                if rec.country_id.code != "BR":
                    rec.cte40_choice7 = "cte40_idEstrangeiro"
                else:
                    rec.cte40_choice7 = "cte40_CPF"
                rec.cte40_choice8 = "cte40_CNPJ"
                rec.cte40_choice19 = "cte40_CNPJ"
                rec.cnpj_cpf = cnpj_cpf.formata(str(rec.cte40_CPF))
