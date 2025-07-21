# Copyright 2019 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from erpbrasil.base.fiscal import cnpj_cpf
from erpbrasil.base.misc import format_zipcode, punctuation_rm

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


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
        compute="_compute_nfe_data",
        inverse="_inverse_nfe40_CNPJ",
        store=True,
        compute_sudo=True,
    )
    nfe40_CPF = fields.Char(
        compute="_compute_nfe_data",
        inverse="_inverse_nfe40_CPF",
        store=True,
        compute_sudo=True,
    )
    nfe40_xLgr = fields.Char(
        readonly=True,
        compute="_compute_nfe40_ender",
        inverse="_inverse_nfe40_ender",
        compute_sudo=True,
    )
    nfe40_nro = fields.Char(
        readonly=True,
        compute="_compute_nfe40_ender",
        inverse="_inverse_nfe40_ender",
        compute_sudo=True,
    )
    nfe40_xCpl = fields.Char(
        readonly=True,
        compute="_compute_nfe40_ender",
        inverse="_inverse_nfe40_ender",
        compute_sudo=True,
    )
    nfe40_xBairro = fields.Char(
        readonly=True,
        compute="_compute_nfe40_ender",
        inverse="_inverse_nfe40_ender",
        compute_sudo=True,
    )
    nfe40_cMun = fields.Char(
        readonly=True,
        compute="_compute_nfe40_ender",
        inverse="_inverse_nfe40_ender",
        compute_sudo=True,
    )
    nfe40_xMun = fields.Char(
        readonly=True,
        compute="_compute_nfe40_ender",
        inverse="_inverse_nfe40_ender",
        compute_sudo=True,
    )
    # Char overriding Selection:
    nfe40_UF = fields.Char(
        compute="_compute_nfe40_ender",
        inverse="_inverse_nfe40_ender",
        compute_sudo=True,
    )

    # Emit
    nfe40_choice_emit = fields.Selection(
        selection=[("nfe40_CNPJ", "CNPJ"), ("nfe40_CPF", "CPF")],
        string="CNPJ/CPF do Emitente",
        compute="_compute_nfe_data",
        compute_sudo=True,
    )

    # nfe.40.tendereco
    nfe40_CEP = fields.Char(
        compute="_compute_nfe_data", inverse="_inverse_nfe40_CEP", compute_sudo=True
    )
    nfe40_cPais = fields.Char(
        compute="_compute_nfe40_ender",
        inverse="_inverse_nfe40_ender",
        compute_sudo=True,
    )
    nfe40_xPais = fields.Char(
        compute="_compute_nfe40_ender",
        inverse="_inverse_nfe40_ender",
        compute_sudo=True,
    )
    nfe40_fone = fields.Char(
        compute="_compute_nfe_data", inverse="_inverse_nfe40_fone", compute_sudo=True
    )

    # nfe.40.dest
    nfe40_xNome = fields.Char(related="legal_name")
    nfe40_xFant = fields.Char(related="name", string="Nome Fantasia")
    nfe40_enderDest = fields.Many2one(
        comodel_name="res.partner", compute="_compute_nfe40_enderDest"
    )
    nfe40_indIEDest = fields.Selection(related="ind_ie_dest")
    nfe40_IE = fields.Char(
        compute="_compute_nfe_data",
        inverse="_inverse_nfe40_IE",
        compute_sudo=True,
    )
    nfe40_ISUF = fields.Char(related="l10n_br_isuf_code")
    nfe40_email = fields.Char(related="email")
    nfe40_xEnder = fields.Char(compute="_compute_nfe40_xEnder")

    # nfe.40.infresptec
    nfe40_xContato = fields.Char(related="legal_name")

    nfe40_choice_tlocal = fields.Selection(
        selection=[("nfe40_CNPJ", "CNPJ"), ("nfe40_CPF", "CPF")],
        string="CNPJ/CPF do Parceiro",
        compute="_compute_nfe_data",
        compute_sudo=True,
    )

    nfe40_choice_dest = fields.Selection(
        selection=[
            ("nfe40_CNPJ", "CNPJ"),
            ("nfe40_CPF", "CPF"),
            ("nfe40_idEstrangeiro", "idEstrangeiro"),
        ],
        compute="_compute_nfe_data",
        compute_sudo=True,
        string="CNPJ/CPF/idEstrangeiro",
    )

    # nfe.40.autXML
    nfe40_choice_autxml = fields.Selection(
        selection=[("nfe40_CNPJ", "CNPJ"), ("nfe40_CPF", "CPF")],
        string="CNPJ/CPF do Parceiro Autorizado",
        compute="_compute_nfe_data",
        compute_sudo=True,
    )

    # nfe.40.transporta
    nfe40_choice_transporta = fields.Selection(
        selection=[
            ("nfe40_CNPJ", "CNPJ"),
            ("nfe40_CPF", "CPF"),
        ],
        string="CNPJ or CPF",
        compute="_compute_nfe_data",
        compute_sudo=True,
    )

    is_anonymous_consumer = fields.Boolean(
        help="Indicates that the partner is an anonymous consumer",
    )

    def _compute_nfe40_xEnder(self):
        for rec in self:
            # Campos do endereço são separados no Emitente e Destinatario
            # porém no caso da Transportadadora o campo do endereço é maior
            # porém sem os detalhes como complemento e bairro, mas
            # operacionalmente são importantes, por isso caso existam o
            # Complemento e o Bairro é melhor agrega-los.
            # campo street retorna "street_name, street_number"
            endereco = rec.street
            if rec.street2:
                endereco += " - " + rec.street2
            if rec.district:
                endereco += " - " + rec.district

            rec.nfe40_xEnder = endereco

    def _compute_nfe40_enderDest(self):
        for rec in self:
            rec.nfe40_enderDest = rec.id

    @api.depends("company_type", "l10n_br_ie_code", "cnpj_cpf", "country_id")
    def _compute_nfe_data(self):
        """Set schema data which are not just related fields"""
        for rec in self:
            cnpj_cpf = punctuation_rm(rec.cnpj_cpf)
            if cnpj_cpf:
                if rec.country_id.code != "BR":
                    rec.nfe40_choice_dest = "nfe40_idEstrangeiro"
                    rec.nfe40_choice_tlocal = False
                elif rec.is_company:
                    rec.nfe40_choice_tlocal = "nfe40_CNPJ"
                    rec.nfe40_choice_emit = "nfe40_CNPJ"
                    rec.nfe40_choice_dest = "nfe40_CNPJ"
                    rec.nfe40_choice_autxml = "nfe40_CNPJ"
                    rec.nfe40_choice_transporta = "nfe40_CNPJ"
                    rec.nfe40_CNPJ = cnpj_cpf
                    rec.nfe40_CPF = None
                else:
                    rec.nfe40_choice_tlocal = "nfe40_CPF"
                    rec.nfe40_choice_emit = "nfe40_CPF"
                    rec.nfe40_choice_dest = "nfe40_CPF"
                    rec.nfe40_choice_autxml = "nfe40_CPF"
                    rec.nfe40_choice_transporta = "nfe40_CPF"
                    rec.nfe40_CPF = cnpj_cpf
                    rec.nfe40_CNPJ = None
            else:
                rec.nfe40_choice_tlocal = False
                rec.nfe40_choice_emit = False
                rec.nfe40_choice_dest = False
                rec.nfe40_choice_autxml = False
                rec.nfe40_choice_transporta = False
                rec.nfe40_CNPJ = ""
                rec.nfe40_CPF = ""

            if rec.l10n_br_ie_code:
                rec.nfe40_IE = punctuation_rm(rec.l10n_br_ie_code)
            else:
                rec.nfe40_IE = None

            rec.nfe40_CEP = punctuation_rm(rec.zip)
            rec.nfe40_fone = punctuation_rm(rec.phone or "").replace(" ", "")

    def _inverse_nfe40_CNPJ(self):
        for rec in self:
            if rec.nfe40_CNPJ:
                rec.is_company = True
                rec.nfe40_choice_tlocal = "nfe40_CPF"
                rec.nfe40_choice_emit = "nfe40_CPF"
                if rec.country_id.code != "BR":
                    rec.nfe40_choice_dest = "nfe40_idEstrangeiro"
                else:
                    rec.nfe40_choice_dest = "nfe40_CNPJ"
                rec.nfe40_choice_dest = "nfe40_CPF"
                rec.nfe40_choice_autxml = "nfe40_CPF"
                rec.nfe40_choice_transporta = "nfe40_CPF"
                rec.cnpj_cpf = cnpj_cpf.formata(str(rec.nfe40_CNPJ))

    def _inverse_nfe40_CPF(self):
        for rec in self:
            if rec.nfe40_CPF:
                rec.is_company = False
                rec.nfe40_choice_tlocal = "nfe40_CNPJ"
                rec.nfe40_choice_emit = "nfe40_CNPJ"
                if rec.country_id.code != "BR":
                    rec.nfe40_choice_dest = "nfe40_idEstrangeiro"
                else:
                    rec.nfe40_choice_dest = "nfe40_CPF"
                rec.nfe40_choice_autxml = "nfe40_CNPJ"
                rec.nfe40_choice_transporta = "nfe40_CNPJ"
                rec.cnpj_cpf = cnpj_cpf.formata(str(rec.nfe40_CPF))

    def _inverse_nfe40_IE(self):
        for rec in self:
            if rec.nfe40_IE:
                rec.l10n_br_ie_code = str(rec.nfe40_IE)

    def _inverse_nfe40_CEP(self):
        for rec in self:
            if rec.nfe40_CEP:
                country_code = rec.country_id.code if rec.country_id else "BR"
                rec.zip = format_zipcode(rec.nfe40_CEP, country_code)

    def _inverse_nfe40_fone(self):
        for rec in self:
            if rec.nfe40_fone:
                rec.phone = rec.nfe40_fone

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        if model is not None and model != self:
            return False

        if parent_dict.get("nfe40_CNPJ", False):
            rec_dict["cnpj_cpf"] = parent_dict["nfe40_CNPJ"]

        if rec_dict.get("nfe40_CNPJ", False):
            rec_dict["cnpj_cpf"] = rec_dict["nfe40_CNPJ"]

        if rec_dict.get("cnpj_cpf", False):
            domain_cnpj = [
                "|",
                ("cnpj_cpf_stripped", "=", rec_dict["cnpj_cpf"]),
                ("vat", "=", cnpj_cpf.formata(rec_dict["cnpj_cpf"])),
            ]
            match = self.search(domain_cnpj, limit=1)
            if match:
                return match.id

        vals = self._prepare_import_dict(
            rec_dict, model=model, parent_dict=parent_dict, defaults_model=model
        )
        if self._context.get("dry_run", False):
            rec_id = self.new(vals).id
        else:
            rec_id = self.with_context(parent_dict=parent_dict).create(vals).id
        return rec_id

    def _export_field(self, xsd_field, class_obj, member_spec, export_value=None):
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

            if xsd_field == self.nfe40_choice_tlocal:
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
                return self.vat or self.cnpj_cpf or self.l10n_br_rg_code or "EXTERIOR"

        return super()._export_field(xsd_field, class_obj, member_spec, export_value)

    ##########################
    # NF-e tag: enderXXX
    # Compute Methods
    ##########################

    @api.depends(
        "street_name",
        "street_number",
        "street2",
        "district",
        "city_id",
        "state_id",
        "country_id",
    )
    def _compute_nfe40_ender(self):
        for rec in self:
            if not rec.is_anonymous_consumer:
                rec.nfe40_xLgr = rec.street_name
                rec.nfe40_nro = rec.street_number
                rec.nfe40_xCpl = rec.street2
                rec.nfe40_xBairro = rec.district
                rec.nfe40_cMun = rec.city_id.ibge_code
                rec.nfe40_xMun = rec.city_id.name
                rec.nfe40_UF = rec.state_id.code
                rec.nfe40_cPais = rec.country_id.bc_code
                rec.nfe40_xPais = rec.country_id.name.replace("Brazil", "Brasil")
            else:
                rec.nfe40_xLgr = None
                rec.nfe40_nro = None
                rec.nfe40_xCpl = None
                rec.nfe40_xBairro = None
                rec.nfe40_cMun = None
                rec.nfe40_xMun = None
                rec.nfe40_UF = None
                rec.nfe40_cPais = None
                rec.nfe40_xPais = None

    def _inverse_nfe40_ender(self):
        for rec in self:
            if rec.nfe40_cMun and rec.nfe40_cPais and rec.nfe40_UF:
                city_id = self.env["res.city"].search(
                    [("ibge_code", "=", rec.nfe40_cMun)]
                )
                country_id = self.env["res.country"].search(
                    [("bc_code", "=", rec.nfe40_cPais)]
                )
                state_id = self.env["res.country.state"].search(
                    [("code", "=", rec.nfe40_UF), ("country_id", "=", country_id.id)]
                )

                rec.street_name = rec.nfe40_xLgr
                rec.street_number = rec.nfe40_nro
                rec.street2 = rec.nfe40_xCpl
                rec.district = rec.nfe40_xBairro
                rec.city_id = city_id
                rec.country_id = country_id
                rec.state_id = state_id
