# Copyright 2019 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base.fiscal import cnpj_cpf
    from erpbrasil.base.misc import punctuation_rm, format_zipcode
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class ResPartner(spec_models.SpecModel):
    # NOTE TODO
    # dest has a m2o tendereco. tlocal and tendereco are really similar...
    # what happen to m2o to tendereco if we don't inherit from tendereco?
    # should we stack tendereco from dest? will m2o to tendereco work?
    # can we use related fields and context views to avoid troubles?
    _name = "res.partner"
    _inherit = [
        "res.partner",
        "nfe.40.tendereco",
        "nfe.40.tlocal",
        "nfe.40.dest",
        "nfe.40.tenderemi",
        "nfe.40.tinfresptec",
        "nfe.40.transporta",
        "nfe.40.autxml",
    ]
    _nfe_search_keys = ["nfe40_CNPJ", "nfe40_CPF", "nfe40_xNome"]

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

    # nfe.40.tlocal / nfe.40.enderEmit / 'nfe.40.enderDest
    # TODO: may be not store=True -> then override match
    nfe40_CNPJ = fields.Char(
        compute="_compute_nfe_data", inverse="_inverse_nfe40_CNPJ", store=True
    )
    nfe40_CPF = fields.Char(
        compute="_compute_nfe_data", inverse="_inverse_nfe40_CPF", store=True
    )
    nfe40_xLgr = fields.Char(related="street_name", readonly=True)
    nfe40_nro = fields.Char(related="street_number", readonly=True)
    nfe40_xCpl = fields.Char(related="street2", readonly=True)
    nfe40_xBairro = fields.Char(related="district", readonly=True)
    nfe40_cMun = fields.Char(related="city_id.ibge_code", readonly=True)
    nfe40_xMun = fields.Char(related="city_id.name", readonly=True)
    # Char overriding Selection:
    nfe40_UF = fields.Char(related="state_id.code")

    # nfe.40.tendereco
    nfe40_CEP = fields.Char(
        compute="_compute_nfe_data", inverse="_inverse_nfe40_CEP"
    )
    nfe40_cPais = fields.Char(related="country_id.bc_code")
    nfe40_xPais = fields.Char(related="country_id.name")
    nfe40_fone = fields.Char(
        compute="_compute_nfe_data", inverse="_inverse_nfe40_fone"
    )

    # nfe.40.dest
    nfe40_xNome = fields.Char(related="legal_name")
    nfe40_xFant = fields.Char(related="name", string="Nome Fantasia")
    nfe40_enderDest = fields.Many2one(
        comodel_name="res.partner", compute="_compute_nfe40_enderDest"
    )
    nfe40_indIEDest = fields.Selection(related="ind_ie_dest")
    nfe40_IE = fields.Char(compute="_compute_nfe_data", inverse="_inverse_nfe40_IE")
    nfe40_ISUF = fields.Char(related="suframa")
    nfe40_email = fields.Char(related="email")
    nfe40_xEnder = fields.Char(compute="_compute_nfe40_xEnder")

    # nfe.40.infresptec
    nfe40_xContato = fields.Char(related="legal_name")

    nfe40_choice2 = fields.Selection(
        selection=[("nfe40_CNPJ", "CNPJ"), ("nfe40_CPF", "CPF")],
        string="CNPJ/CPF do Parceiro",
    )

    nfe40_choice7 = fields.Selection(
        selection=[
            ("nfe40_CNPJ", "CNPJ"),
            ("nfe40_CPF", "CPF"),
            ("nfe40_idEstrangeiro", "idEstrangeiro"),
        ],
        compute="_compute_nfe_data",
        string="CNPJ/CPF/idEstrangeiro",
    )

    # nfe.40.autXML
    nfe40_choice8 = fields.Selection(
        selection=[("nfe40_CNPJ", "CNPJ"), ("nfe40_CPF", "CPF")],
        string="CNPJ/CPF do Parceiro Autorizado",
    )

    # nfe.40.transporta
    nfe40_choice19 = fields.Selection(
        selection=[
            ("nfe40_CNPJ", "CNPJ"),
            ("nfe40_CPF", "CPF"),
        ],
        string="CNPJ or CPF",
    )

    def _compute_nfe40_xEnder(self):
        for rec in self:
            rec.nfe40_xEnder = ", ".join(
                [i for i in [rec.street, rec.street_number] if i]
            )
            if rec.street2:
                rec.nfe40_xEnder = " - ".join((rec.nfe40_xEnder, rec.street2))

    def _compute_nfe40_enderDest(self):
        for rec in self:
            rec.nfe40_enderDest = rec.id

    @api.depends("company_type", "inscr_est", "cnpj_cpf", "country_id")
    def _compute_nfe_data(self):
        """Set schema data which are not just related fields"""
        for rec in self:
            cnpj_cpf = punctuation_rm(rec.cnpj_cpf)
            if cnpj_cpf:
                if rec.country_id.code != "BR":
                    rec.nfe40_choice7 = "nfe40_idEstrangeiro"
                elif rec.is_company:
                    rec.nfe40_choice7 = "nfe40_CNPJ"
                    rec.nfe40_CNPJ = cnpj_cpf
                else:
                    rec.nfe40_choice7 = "nfe40_CPF"
                    rec.nfe40_CPF = cnpj_cpf

            if rec.inscr_est and rec.is_company:
                rec.nfe40_IE = punctuation_rm(rec.inscr_est)
            else:
                rec.nfe40_IE = None

            rec.nfe40_CEP = punctuation_rm(rec.zip)
            rec.nfe40_fone = punctuation_rm(rec.phone or "").replace(" ", "")

    def _inverse_nfe40_CNPJ(self):
        for rec in self:
            if rec.nfe40_CNPJ:
                rec.is_company = True
                rec.cnpj_cpf = cnpj_cpf.formata(str(rec.nfe40_CNPJ))

    def _inverse_nfe40_CPF(self):
        for rec in self:
            if rec.nfe40_CPF:
                rec.is_company = False
                rec.cnpj_cpf = cnpj_cpf.formata(str(rec.nfe40_CPF))

    def _inverse_nfe40_IE(self):
        for rec in self:
            if rec.nfe40_IE:
                rec.inscr_est = str(rec.nfe40_IE)

    def _inverse_nfe40_CEP(self):
        for rec in self:
            if rec.nfe40_CEP:
                country_code = rec.country_id.code if rec.country_id else "BR"
                rec.zip = format_zipcode(rec.nfe40_CEP, country_code)

    def _inverse_nfe40_fone(self):
        for rec in self:
            if rec.nfe40_fone:
                rec.phone = rec.nfe40_fone

    def _export_field(self, xsd_field, class_obj, member_spec):
        # Se a NF-e é emitida em homologação altera o nome do destinatário
        if (
            xsd_field == "nfe40_xNome"
            and class_obj._name == "nfe.40.dest"
            and self.env.context.get("tpAmb") == "2"
        ):
            return "NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL"

        if xsd_field in ("nfe40_CNPJ", "nfe40_CPF"):
            # Caso o CNPJ/CPF esteja em branco e o parceiro tenha um parent_id
            # É exportado o CNPJ/CPF do parent_id é importate para o endereço
            # de entrega/retirada
            if not self.cnpj_cpf and self.parent_id:
                cnpj_cpf = punctuation_rm(self.parent_id.cnpj_cpf)
            else:
                cnpj_cpf = punctuation_rm(self.cnpj_cpf)

            if xsd_field == self.nfe40_choice2:
                return cnpj_cpf

        if self.country_id.code != "BR":
            if xsd_field == "nfe40_xBairro":
                return "EX"

            if xsd_field == "nfe40_xMun":
                return "EXTERIOR"

            if xsd_field == "nfe40_cMun":
                return "9999999"

            if xsd_field == "nfe40_UF":
                return "EX"
            if xsd_field == "nfe40_idEstrangeiro":
                return self.vat or self.cnpj_cpf or self.rg or "EXTERIOR"

        return super()._export_field(xsd_field, class_obj, member_spec)
