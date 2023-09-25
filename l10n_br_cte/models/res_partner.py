# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base.misc import format_zipcode, punctuation_rm
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
    _binding_module = "nfelib.cte.bindings.v4_0.cte_tipos_basico_v4_00"
    _field_prefix = "cte40_"

    cte40_choice_cnpj_cpf = fields.Selection(
        selection=[("cte40_CNPJ", "CNPJ"), ("cte40_CPF", "CPF")],
        string="CNPJ/CPF do Parceiro",
    )

    cte40_CNPJ = fields.Char(
        compute="_compute_cte_data",
        store=True,
    )

    cte40_CPF = fields.Char(
        compute="_compute_cte_data",
        store=True,
    )

    # Same problem with Tendereco that NFE has, it has to use m2o fields
    cte40_enderToma = fields.Many2one(
        comodel_name="res.partner", compute="_compute_cte40_ender"
    )

    cte40_enderReme = fields.Many2one(
        comodel_name="res.partner", compute="_compute_cte40_ender"
    )

    cte40_enderDest = fields.Many2one(
        comodel_name="res.partner", compute="_compute_cte40_ender"
    )

    cte40_enderExped = fields.Many2one(
        comodel_name="res.partner", compute="_compute_cte40_ender"
    )

    # enderToma/enderEmit/enderReme
    cte40_xLgr = fields.Char(related="street_name", readonly=True)
    cte40_nro = fields.Char(related="street_number", readonly=True)
    cte40_xCpl = fields.Char(related="street2", readonly=True)
    cte40_xBairro = fields.Char(related="district", readonly=True)
    cte40_cMun = fields.Char(related="city_id.ibge_code", readonly=True)
    cte40_xMun = fields.Char(related="city_id.name", readonly=True)
    cte40_UF = fields.Char(related="state_id.code")
    cte40_CEP = fields.Char(
        compute="_compute_cep",
        inverse="_inverse_cte40_CEP",
        compute_sudo=True,
        store=True,
    )
    cte40_cPais = fields.Char(
        related="country_id.bc_code",
    )
    cte40_xPais = fields.Char(
        related="country_id.name",
    )

    cte40_IE = fields.Char(related="inscr_est")

    cte40_xNome = fields.Char(related="legal_name")

    def _compute_cte40_ender(self):
        for rec in self:
            rec.cte40_enderToma = rec.id
            rec.cte40_enderReme = rec.id
            rec.cte40_enderDest = rec.id
            rec.cte40_enderExped = rec.id

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

    def _inverse_cte40_CEP(self):
        for rec in self:
            if rec.cte40_CEP:
                country_code = rec.country_id.code if rec.country_id else "BR"
                rec.zip = format_zipcode(rec.cte40_CEP, country_code)

    def _compute_cep(self):
        for rec in self:
            rec.cte40_CEP = punctuation_rm(rec.zip)

    def _export_field(self, xsd_field, class_obj, member_spec, export_value=None):
        if not self.cnpj_cpf and self.parent_id:
            cnpj_cpf = punctuation_rm(self.parent_id.cnpj_cpf)
        else:
            cnpj_cpf = punctuation_rm(self.cnpj_cpf)

        if xsd_field == self.cte40_choice_cnpj_cpf:
            return cnpj_cpf

        if self.country_id.code != "BR":
            if xsd_field == "cte40_xBairro":
                return "EX"

            if xsd_field == "cte40_xMun":
                return "EXTERIOR"

            if xsd_field == "cte40_cMun":
                return "9999999"

            if xsd_field == "cte40_UF":
                return "EX"
        return super()._export_field(xsd_field, class_obj, member_spec, export_value)
