# Copyright 2023 KMEE INFORMATICA LTDA
# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from erpbrasil.base.fiscal import cnpj_cpf

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
        "cte.40.tcte_rem",
        "cte.40.exped",
        "cte.40.receb",
        "cte.40.tresptec",
        "cte.40.tcte_autxml",
        "cte.40.tenderfer",
    ]
    _cte_search_keys = ["cte40_CNPJ", "cte40_CPF", "cte40_xNome"]
    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_modal_dutoviario_v4_00"
    )

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

    # cte.40.tlocal / cte.40.enderEmit / 'cte.40.enderDest
    # TODO: may be not store=True -> then override match

    cte40_cInt = fields.Char(
        string="Código interno da Ferrovia envolvida",
        help="Código interno da Ferrovia envolvida\nUso da transportadora",
    )

    cte40_CNPJ = fields.Char(
        compute="_compute_cte_data",
        inverse="_inverse_cte40_CNPJ",
        store=True,
        compute_sudo=True,
    )
    cte40_CPF = fields.Char(
        compute="_compute_cte_data",
        inverse="_inverse_cte40_CPF",
        store=True,
        compute_sudo=True,
    )
    cte40_xLgr = fields.Char(
        readonly=True,
        compute="_compute_cte40_ender",
        inverse="_inverse_cte40_ender",
        compute_sudo=True,
    )
    cte40_nro = fields.Char(
        readonly=True,
        compute="_compute_cte40_ender",
        inverse="_inverse_cte40_ender",
        compute_sudo=True,
    )
    cte40_xCpl = fields.Char(
        readonly=True,
        compute="_compute_cte40_ender",
        inverse="_inverse_cte40_ender",
        compute_sudo=True,
    )
    cte40_xBairro = fields.Char(
        readonly=True,
        compute="_compute_cte40_ender",
        inverse="_inverse_cte40_ender",
        compute_sudo=True,
    )
    cte40_cMun = fields.Char(
        readonly=True,
        compute="_compute_cte40_ender",
        inverse="_inverse_cte40_ender",
        compute_sudo=True,
    )
    cte40_xMun = fields.Char(
        readonly=True,
        compute="_compute_cte40_ender",
        inverse="_inverse_cte40_ender",
        compute_sudo=True,
    )
    # Char overriding Selection:
    cte40_UF = fields.Char(
        compute="_compute_cte40_ender",
        inverse="_inverse_cte40_ender",
        compute_sudo=True,
    )

    # Same problem with Tendereco that cte has, it has to use m2o fields
    cte40_enderToma = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_cte40_enderToma",
        compute_sudo=True,
    )

    cte40_enderReme = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_cte40_enderReme",
        compute_sudo=True,
    )

    cte40_enderDest = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_cte40_enderDest",
        compute_sudo=True,
    )

    cte40_enderExped = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_cte40_enderExped",
        compute_sudo=True,
    )

    cte40_enderReceb = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_cte40_enderReceb",
        compute_sudo=True,
    )

    cte40_enderFerro = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_cte40_enderFerro",
        compute_sudo=True,
    )

    # Emit
    cte40_choice_emit = fields.Selection(
        selection=[("cte40_CNPJ", "CNPJ"), ("cte40_CPF", "CPF")],
        string="CNPJ/CPF do Emitente",
        compute="_compute_cte_data",
        compute_sudo=True,
    )

    # cte.40.tendereco
    cte40_CEP = fields.Char(
        compute="_compute_cte_data", inverse="_inverse_cte40_CEP", compute_sudo=True
    )
    cte40_cPais = fields.Char(
        compute="_compute_cte40_ender",
        inverse="_inverse_cte40_ender",
        compute_sudo=True,
    )
    cte40_xPais = fields.Char(
        compute="_compute_cte40_ender",
        inverse="_inverse_cte40_ender",
        compute_sudo=True,
    )
    cte40_fone = fields.Char(
        compute="_compute_cte_data", inverse="_inverse_cte40_fone", compute_sudo=True
    )

    # cte.40.dest
    cte40_xNome = fields.Char(related="legal_name")
    cte40_xFant = fields.Char(related="name", string="Nome Fantasia")
    cte40_IE = fields.Char(
        compute="_compute_cte_data",
        inverse="_inverse_cte40_IE",
        compute_sudo=True,
    )
    cte40_ISUF = fields.Char(related="l10n_br_isuf_code")
    cte40_email = fields.Char(related="email")
    cte40_xEnder = fields.Char(
        compute="_compute_cte40_xEnder",
        compute_sudo=True,
    )

    # cte.40.infresptec
    cte40_xContato = fields.Char(related="legal_name")

    cte40_choice_tlocal = fields.Selection(
        selection=[("cte40_CNPJ", "CNPJ"), ("cte40_CPF", "CPF")],
        string="CNPJ/CPF do Parceiro",
        compute="_compute_cte_data",
        compute_sudo=True,
    )

    cte40_choice_toma = fields.Selection(
        selection=[
            ("cte40_CNPJ", "CNPJ"),
            ("cte40_CPF", "CPF"),
            ("cte40_idEstrangeiro", "idEstrangeiro"),
        ],
        compute="_compute_cte_data",
        compute_sudo=True,
        string="CNPJ/CPF/idEstrangeiro",
    )

    cte40_choice_dest = fields.Selection(
        selection=[
            ("cte40_CNPJ", "CNPJ"),
            ("cte40_CPF", "CPF"),
            ("cte40_idEstrangeiro", "idEstrangeiro"),
        ],
        compute="_compute_cte_data",
        compute_sudo=True,
        string="CNPJ/CPF/idEstrangeiro",
    )

    cte40_choice_rem = fields.Selection(
        selection=[
            ("cte40_CNPJ", "CNPJ"),
            ("cte40_CPF", "CPF"),
            ("cte40_idEstrangeiro", "idEstrangeiro"),
        ],
        compute="_compute_cte_data",
        compute_sudo=True,
        string="CNPJ/CPF/idEstrangeiro",
    )

    cte40_choice_dest = fields.Selection(
        selection=[
            ("cte40_CNPJ", "CNPJ"),
            ("cte40_CPF", "CPF"),
            ("cte40_idEstrangeiro", "idEstrangeiro"),
        ],
        compute="_compute_cte_data",
        compute_sudo=True,
        string="CNPJ/CPF/idEstrangeiro",
    )

    cte40_choice_receb = fields.Selection(
        selection=[
            ("cte40_CNPJ", "CNPJ"),
            ("cte40_CPF", "CPF"),
            ("cte40_idEstrangeiro", "idEstrangeiro"),
        ],
        compute="_compute_cte_data",
        compute_sudo=True,
        string="CNPJ/CPF/idEstrangeiro",
    )

    cte40_choice_exped = fields.Selection(
        selection=[
            ("cte40_CNPJ", "CNPJ"),
            ("cte40_CPF", "CPF"),
            ("cte40_idEstrangeiro", "idEstrangeiro"),
        ],
        compute="_compute_cte_data",
        compute_sudo=True,
        string="CNPJ/CPF/idEstrangeiro",
    )

    # cte.40.autXML
    cte40_choice_autxml = fields.Selection(
        selection=[("cte40_CNPJ", "CNPJ"), ("cte40_CPF", "CPF")],
        string="CNPJ/CPF do Parceiro Autorizado",
        compute="_compute_cte_data",
        compute_sudo=True,
    )

    # cte.40.transporta
    cte40_choice_transporta = fields.Selection(
        selection=[
            ("cte40_CNPJ", "CNPJ"),
            ("cte40_CPF", "CPF"),
        ],
        string="CNPJ or CPF",
        compute="_compute_cte_data",
        compute_sudo=True,
    )

    def _compute_cte40_xEnder(self):
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

            rec.cte40_xEnder = endereco

    def _compute_cte40_enderToma(self):
        for rec in self:
            rec.cte40_enderToma = rec.id

    def _compute_cte40_enderDest(self):
        for rec in self:
            rec.cte40_enderDest = rec.id

    def _compute_cte40_enderReme(self):
        for rec in self:
            rec.cte40_enderReme = rec.id

    def _compute_cte40_enderReceb(self):
        for rec in self:
            rec.cte40_enderReceb = rec.id

    def _compute_cte40_enderExped(self):
        for rec in self:
            rec.cte40_enderExped = rec.id

    def _compute_cte40_enderFerro(self):
        for rec in self:
            rec.cte40_enderFerro = rec.id

    @api.depends("company_type", "l10n_br_ie_code", "cnpj_cpf", "country_id")
    def _compute_cte_data(self):
        """Set schema data which are not just related fields"""
        for rec in self:
            cnpj_cpf = punctuation_rm(rec.cnpj_cpf)
            if cnpj_cpf:
                if rec.country_id.code != "BR":
                    rec.cte40_choice_toma = "cte40_idEstrangeiro"
                    rec.cte40_choice_dest = "cte40_idEstrangeiro"
                    rec.cte40_choice_rem = "cte40_idEstrangeiro"
                    rec.cte40_choice_receb = "cte40_idEstrangeiro"
                    rec.cte40_choice_exped = "cte40_idEstrangeiro"
                    rec.cte40_choice_tlocal = False
                elif rec.is_company:
                    rec.cte40_choice_tlocal = "cte40_CNPJ"
                    rec.cte40_choice_toma = "cte40_CNPJ"
                    rec.cte40_choice_emit = "cte40_CNPJ"
                    rec.cte40_choice_dest = "cte40_CNPJ"
                    rec.cte40_choice_rem = "cte40_CNPJ"
                    rec.cte40_choice_receb = "cte40_CNPJ"
                    rec.cte40_choice_exped = "cte40_CNPJ"
                    rec.cte40_choice_autxml = "cte40_CNPJ"
                    rec.cte40_choice_transporta = "cte40_CNPJ"
                    rec.cte40_CNPJ = cnpj_cpf
                    rec.cte40_CPF = None
                else:
                    rec.cte40_choice_tlocal = "cte40_CPF"
                    rec.cte40_choice_toma = "cte40_CPF"
                    rec.cte40_choice_emit = "cte40_CPF"
                    rec.cte40_choice_dest = "cte40_CPF"
                    rec.cte40_choice_rem = "cte40_CPF"
                    rec.cte40_choice_receb = "cte40_CPF"
                    rec.cte40_choice_exped = "cte40_CPF"
                    rec.cte40_choice_autxml = "cte40_CPF"
                    rec.cte40_choice_transporta = "cte40_CPF"
                    rec.cte40_CPF = cnpj_cpf
                    rec.cte40_CNPJ = None
            else:
                rec.cte40_choice_tlocal = False
                rec.cte40_choice_toma = False
                rec.cte40_choice_emit = False
                rec.cte40_choice_dest = False
                rec.cte40_choice_rem = False
                rec.cte40_choice_receb = False
                rec.cte40_choice_exped = False
                rec.cte40_choice_autxml = False
                rec.cte40_choice_transporta = False
                rec.cte40_CNPJ = ""
                rec.cte40_CPF = ""

            if rec.l10n_br_ie_code:
                rec.cte40_IE = punctuation_rm(rec.l10n_br_ie_code)
            else:
                rec.cte40_IE = None

            rec.cte40_CEP = punctuation_rm(rec.zip)
            rec.cte40_fone = punctuation_rm(rec.phone or "").replace(" ", "")

    def _inverse_cte40_CNPJ(self):
        for rec in self:
            if rec.cte40_CNPJ:
                rec.is_company = True
                rec.cte40_choice_tlocal = "cte40_CPF"
                rec.cte40_choice_emit = "cte40_CPF"
                if rec.country_id.code != "BR":
                    rec.cte40_choice_toma = "cte40_idEstrangeiro"
                    rec.cte40_choice_dest = "cte40_idEstrangeiro"
                    rec.cte40_choice_rem = "cte40_idEstrangeiro"
                    rec.cte40_choice_receb = "cte40_idEstrangeiro"
                    rec.cte40_choice_exped = "cte40_idEstrangeiro"
                else:
                    rec.cte40_choice_toma = "cte40_CNPJ"
                    rec.cte40_choice_dest = "cte40_CNPJ"
                    rec.cte40_choice_rem = "cte40_CNPJ"
                    rec.cte40_choice_receb = "cte40_CNPJ"
                    rec.cte40_choice_exped = "cte40_CNPJ"
                rec.cte40_choice_toma = "cte40_CPF"
                rec.cte40_choice_dest = "cte40_CPF"
                rec.cte40_choice_rem = "cte40_CPF"
                rec.cte40_choice_receb = "cte40_CPF"
                rec.cte40_choice_exped = "cte40_CPF"
                rec.cte40_choice_autxml = "cte40_CPF"
                rec.cte40_choice_transporta = "cte40_CPF"
                rec.cnpj_cpf = cnpj_cpf.formata(str(rec.cte40_CNPJ))

    def _inverse_cte40_CPF(self):
        for rec in self:
            if rec.cte40_CPF:
                rec.is_company = False
                rec.cte40_choice_tlocal = "cte40_CNPJ"
                rec.cte40_choice_emit = "cte40_CNPJ"
                if rec.country_id.code != "BR":
                    rec.cte40_choice_toma = "cte40_idEstrangeiro"
                    rec.cte40_choice_dest = "cte40_idEstrangeiro"
                    rec.cte40_choice_rem = "cte40_idEstrangeiro"
                    rec.cte40_choice_receb = "cte40_idEstrangeiro"
                    rec.cte40_choice_exped = "cte40_idEstrangeiro"
                else:
                    rec.cte40_choice_toma = "cte40_CPF"
                    rec.cte40_choice_dest = "cte40_CPF"
                    rec.cte40_choice_rem = "cte40_CPF"
                    rec.cte40_choice_receb = "cte40_CPF"
                    rec.cte40_choice_exped = "cte40_CPF"
                rec.cte40_choice_autxml = "cte40_CNPJ"
                rec.cte40_choice_transporta = "cte40_CNPJ"
                rec.cnpj_cpf = cnpj_cpf.formata(str(rec.cte40_CPF))

    def _inverse_cte40_IE(self):
        for rec in self:
            if rec.cte40_IE:
                rec.l10n_br_ie_code = str(rec.cte40_IE)

    def _inverse_cte40_CEP(self):
        for rec in self:
            if rec.cte40_CEP:
                country_code = rec.country_id.code if rec.country_id else "BR"
                rec.zip = format_zipcode(rec.cte40_CEP, country_code)

    def _inverse_cte40_fone(self):
        for rec in self:
            if rec.cte40_fone:
                rec.phone = rec.cte40_fone

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        if model is not None and model != self:
            return False

        if parent_dict.get("cte40_CNPJ", False):
            rec_dict["cnpj_cpf"] = parent_dict["cte40_CNPJ"]

        if rec_dict.get("cte40_CNPJ", False):
            rec_dict["cnpj_cpf"] = rec_dict["cte40_CNPJ"]

        if rec_dict.get("cnpj_cpf", False):
            domain_cnpj = [
                "|",
                ("vat", "=", rec_dict["cnpj_cpf"]),
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
            xsd_field == "cte40_xNome"
            and class_obj._name
            in ["cte.40.tcte_rem", "cte.40.tcte_dest", "cte.40.exped", "cte.40.receb"]
            and self.env.context.get("tpAmb") == "2"
        ):
            return "CTE EMITIDO EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL"

        if xsd_field in ("cte40_CNPJ", "cte40_CPF"):
            # Caso o CNPJ/CPF esteja em branco e o parceiro tenha um parent_id
            # É exportado o CNPJ/CPF do parent_id é importate para o endereço
            # de entrega/retirada
            if not self.cnpj_cpf and self.parent_id:
                cnpj_cpf = punctuation_rm(self.parent_id.cnpj_cpf)
            else:
                cnpj_cpf = punctuation_rm(self.cnpj_cpf)

            if xsd_field == self.cte40_choice_tlocal:
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

            if xsd_field == "cte40_idEstrangeiro":
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
    def _compute_cte40_ender(self):
        for rec in self:
            rec.cte40_xLgr = rec.street_name
            rec.cte40_nro = rec.street_number
            rec.cte40_xCpl = rec.street2
            rec.cte40_xBairro = rec.district
            rec.cte40_cMun = rec.city_id.ibge_code
            rec.cte40_xMun = rec.city_id.name
            rec.cte40_UF = rec.state_id.code
            rec.cte40_cPais = rec.country_id.bc_code
            rec.cte40_xPais = rec.country_id.name.replace("Brazil", "Brasil")

    def _inverse_cte40_ender(self):
        for rec in self:
            if rec.cte40_cMun and rec.cte40_UF:
                city_id = self.env["res.city"].search(
                    [("ibge_code", "=", rec.cte40_cMun)]
                )
                if rec.cte40_cPais:
                    country_id = self.env["res.country"].search(
                        [("bc_code", "=", rec.cte40_cPais)]
                    )
                else:
                    country_id = self.env["res.country"].search([("code", "=", "BR")])

                state_id = self.env["res.country.state"].search(
                    [("code", "=", rec.cte40_UF), ("country_id", "=", country_id.id)]
                )

                rec.street_name = rec.cte40_xLgr
                rec.street_number = rec.cte40_nro
                rec.street2 = rec.cte40_xCpl
                rec.district = rec.cte40_xBairro
                rec.city_id = city_id
                rec.country_id = country_id
                rec.state_id = state_id
