# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.fiscal import cnpj_cpf
from erpbrasil.base.misc import format_zipcode, punctuation_rm

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class ResPartner(spec_models.SpecModel):

    _name = "res.partner"
    _inherit = [
        "res.partner",
        "mdfe.30.tendereco",
        "mdfe.30.tlocal",
        "mdfe.30.tendeemi",
        "mdfe.30.dest",
        "mdfe.30.tresptec",
        "mdfe.30.autxml",
        "mdfe.30.veicreboque_prop",
        "mdfe.30.veictracao_prop",
        "mdfe.30.infcontratante",
        "mdfe.30.infresp",
        "mdfe.30.infseg",
    ]
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_tipos_basico_v3_00"
    _field_prefix = "mdfe30_"
    _mdfe_search_keys = ["mdfe30_CNPJ", "mdfe30_CPF", "mdfe_xNome"]

    @api.model
    def _prepare_import_dict(
        self, values, model=None, parent_dict=None, defaults_model=None
    ):
        values = super()._prepare_import_dict(
            values, model, parent_dict, defaults_model
        )
        if not values.get("name") and values.get("legal_name"):
            values["name"] = values["legal_name"]
        return values

    mdfe30_CNPJ = fields.Char(
        compute="_compute_mdfe_data", inverse="_inverse_mdfe30_CNPJ", store=True
    )

    mdfe30_CPF = fields.Char(
        compute="_compute_mdfe_data", inverse="_inverse_mdfe30_CPF", store=True
    )

    mdfe30_xLgr = fields.Char(
        readonly=True,
        compute="_compute_mdfe30_ender",
        inverse="_inverse_mdfe30_ender",
        compute_sudo=True,
        string="Logradouro - MDFe",
    )

    mdfe30_nro = fields.Char(
        readonly=True,
        compute="_compute_mdfe30_ender",
        inverse="_inverse_mdfe30_ender",
        compute_sudo=True,
        string="Número - MDFe",
    )

    mdfe30_xCpl = fields.Char(
        readonly=True,
        compute="_compute_mdfe30_ender",
        inverse="_inverse_mdfe30_ender",
        compute_sudo=True,
        string="Complemento - MDFe",
    )

    mdfe30_xBairro = fields.Char(
        readonly=True,
        compute="_compute_mdfe30_ender",
        inverse="_inverse_mdfe30_ender",
        compute_sudo=True,
        string="Bairro - MDFe",
    )

    mdfe30_cMun = fields.Char(
        readonly=True,
        compute="_compute_mdfe30_ender",
        inverse="_inverse_mdfe30_ender",
        compute_sudo=True,
        string="Código do Município - MDFe",
    )

    mdfe30_xMun = fields.Char(
        readonly=True,
        compute="_compute_mdfe30_ender",
        inverse="_inverse_mdfe30_ender",
        compute_sudo=True,
        string="Nome do Município - MDFe",
    )

    mdfe30_UF = fields.Char(
        compute="_compute_mdfe30_ender",
        inverse="_inverse_mdfe30_ender",
        compute_sudo=True,
    )

    mdfe30_choice6 = fields.Selection(
        selection=[("mdfe30_CNPJ", "CNPJ"), ("mdfe30_CPF", "CPF")],
        string="CNPJ/CPF do Emitente - MDFe",
        compute="_compute_mdfe_data",
    )

    mdfe30_CEP = fields.Char(
        compute="_compute_mdfe_data", inverse="_inverse_mdfe30_CEP", string="CEP - MDFe"
    )

    mdfe30_cPais = fields.Char(
        compute="_compute_mdfe30_ender",
        inverse="_inverse_mdfe30_ender",
        compute_sudo=True,
        string="Código do País - MDFe",
    )

    mdfe30_xPais = fields.Char(
        compute="_compute_mdfe30_ender",
        inverse="_inverse_mdfe30_ender",
        compute_sudo=True,
        string="Nome do País - MDFe",
    )

    mdfe30_fone = fields.Char(
        compute="_compute_mdfe_data",
        inverse="_inverse_mdfe30_fone",
        string="Telefone MDFe",
    )

    mdfe30_xNome = fields.Char(related="legal_name", string="Nome - MDFe")

    mdfe30_xFant = fields.Char(related="name", string="Nome Fantasia - MDFe")

    mdfe30_IE = fields.Char(
        compute="_compute_mdfe_data",
        inverse="_inverse_mdfe30_IE",
    )

    mdfe30_email = fields.Char(related="email")

    mdfe30_xContato = fields.Char(related="legal_name")

    mdfe30_xSeg = fields.Char(related="legal_name")

    mdfe30_respSeg = fields.Selection(default="1")

    mdfe30_tpProp = fields.Selection(default="0")

    mdfe30_choice8 = fields.Selection(
        selection=[("mdfe30_CNPJ", "CNPJ"), ("mdfe30_CPF", "CPF")],
        string="CNPJ/CPF do Parceiro Autorizado - MDFe",
        compute="_compute_mdfe_data",
    )

    mdfe30_choice9 = fields.Selection(
        selection=[("mdfe30_CNPJ", "CNPJ"), ("mdfe30_CPF", "CPF")],
        string="CNPJ/CPF do Proprietário do Reboque",
        compute="_compute_mdfe_data",
    )

    mdfe30_choice10 = fields.Selection(
        selection=[
            ("mdfe30_CNPJ", "CNPJ"),
            ("mdfe30_CPF", "CPF"),
            ("mdfe30_idEstrangeiro", "idEstrangeiro"),
        ],
        string="CNPJ/CPF/Id Estrangeiro do Contratante",
        compute="_compute_mdfe_data",
    )

    mdfe30_choice11 = fields.Selection(
        selection=[("mdfe30_CNPJ", "CNPJ"), ("mdfe30_CPF", "CPF")],
        string="CNPJ/CPF do Contratante",
        compute="_compute_mdfe_data",
    )

    mdfe30_choice12 = fields.Selection(
        selection=[("mdfe30_CNPJ", "CNPJ"), ("mdfe30_CPF", "CPF")],
        string="CNPJ/CPF do Responsável pelo Seguro da Carga",
        compute="_compute_mdfe_data",
    )

    @api.depends("company_type", "inscr_est", "cnpj_cpf", "country_id")
    def _compute_mdfe_data(self):
        """Set schema data which are not just related fields"""
        for rec in self:
            cnpj_cpf = punctuation_rm(rec.cnpj_cpf)
            if cnpj_cpf:
                if rec.country_id.code != "BR":
                    rec.mdfe30_choice10 = "mdfe30_idEstrangeiro"
                    rec.mdfe30_CNPJ = cnpj_cpf
                elif rec.is_company:
                    rec.mdfe30_choice6 = "mdfe30_CNPJ"
                    rec.mdfe30_choice8 = "mdfe30_CNPJ"
                    rec.mdfe30_choice9 = "mdfe30_CNPJ"
                    rec.mdfe30_choice10 = "mdfe30_CNPJ"
                    rec.mdfe30_choice11 = "mdfe30_CNPJ"
                    rec.mdfe30_choice12 = "mdfe30_CNPJ"
                    rec.mdfe30_CNPJ = cnpj_cpf
                    rec.mdfe30_CPF = None
                else:
                    rec.mdfe30_choice6 = "mdfe30_CPF"
                    rec.mdfe30_choice8 = "mdfe30_CPF"
                    rec.mdfe30_choice9 = "mdfe30_CPF"
                    rec.mdfe30_choice10 = "mdfe30_CPF"
                    rec.mdfe30_choice11 = "mdfe30_CPF"
                    rec.mdfe30_choice12 = "mdfe30_CPF"
                    rec.mdfe30_CPF = cnpj_cpf
                    rec.mdfe30_CNPJ = None
            else:
                rec.mdfe30_choice6 = False
                rec.mdfe30_choice8 = False
                rec.mdfe30_choice9 = False
                rec.mdfe30_choice10 = False
                rec.mdfe30_choice11 = False
                rec.mdfe30_choice12 = False
                rec.mdfe30_CNPJ = ""
                rec.mdfe30_CPF = ""

            if rec.inscr_est:
                rec.mdfe30_IE = punctuation_rm(rec.inscr_est)
            else:
                rec.mdfe30_IE = None

            rec.mdfe30_CEP = punctuation_rm(rec.zip)
            rec.mdfe30_fone = punctuation_rm(rec.phone or "").replace(" ", "")

    def _inverse_mdfe30_CNPJ(self):
        for rec in self:
            if rec.mdfe30_CNPJ:
                rec.is_company = True
                rec.mdfe30_choice6 = "mdfe30_CPF"
                rec.mdfe30_choice8 = "mdfe30_CPF"
                rec.mdfe30_choice9 = "mdfe30_CPF"
                rec.mdfe30_choice10 = "mdfe30_CPF"
                rec.mdfe30_choice11 = "mdfe30_CPF"
                rec.mdfe30_choice12 = "mdfe30_CPF"
                rec.cnpj_cpf = cnpj_cpf.formata(str(rec.mdfe30_CNPJ))

    def _inverse_mdfe30_CPF(self):
        for rec in self:
            if rec.mdfe30_CPF:
                rec.is_company = False
                rec.mdfe30_choice6 = "mdfe30_CNPJ"
                rec.mdfe30_choice8 = "mdfe30_CNPJ"
                rec.mdfe30_choice9 = "mdfe30_CNPJ"
                rec.mdfe30_choice10 = "mdfe30_CNPJ"
                rec.mdfe30_choice11 = "mdfe30_CNPJ"
                rec.mdfe30_choice12 = "mdfe30_CNPJ"
                rec.cnpj_cpf = cnpj_cpf.formata(str(rec.mdfe30_CPF))

    def _inverse_mdfe30_IE(self):
        for rec in self:
            if rec.mdfe30_IE:
                rec.inscr_est = str(rec.mdfe30_IE)

    def _inverse_mdfe30_CEP(self):
        for rec in self:
            if rec.mdfe30_CEP:
                country_code = rec.country_id.code if rec.country_id else "BR"
                rec.zip = format_zipcode(rec.mdfe30_CEP, country_code)

    def _inverse_mdfe30_fone(self):
        for rec in self:
            if rec.mdfe30_fone:
                rec.phone = rec.mdfe30_fone

    @api.depends(
        "street_name",
        "street_number",
        "street2",
        "district",
        "city_id",
        "state_id",
        "country_id",
    )
    def _compute_mdfe30_ender(self):
        for rec in self:
            rec.mdfe30_xLgr = rec.street_name
            rec.mdfe30_nro = rec.street_number
            rec.mdfe30_xCpl = rec.street2
            rec.mdfe30_xBairro = rec.district
            rec.mdfe30_cMun = rec.city_id.ibge_code
            rec.mdfe30_xMun = rec.city_id.name
            rec.mdfe30_UF = rec.state_id.code
            rec.mdfe30_cPais = rec.country_id.bc_code
            rec.mdfe30_xPais = rec.country_id.name

    def _inverse_mdfe30_ender(self):
        for rec in self:
            if rec.mdfe30_cMun and rec.mdfe30_cPais and rec.mdfe30_UF:
                city_id = self.env["res.city"].search(
                    [("ibge_code", "=", rec.mdfe30_cMun)]
                )
                country_id = self.env["res.country"].search(
                    [("bc_code", "=", rec.mdfe30_cPais)]
                )
                state_id = self.env["res.country.state"].search(
                    [("code", "=", rec.mdfe30_UF), ("country_id", "=", country_id.id)]
                )

                rec.street_name = rec.mdfe30_xLgr
                rec.street_number = rec.mdfe30_nro
                rec.street2 = rec.mdfe30_xCpl
                rec.district = rec.mdfe30_xBairro
                rec.city_id = city_id
                rec.country_id = country_id
                rec.state_id = state_id
