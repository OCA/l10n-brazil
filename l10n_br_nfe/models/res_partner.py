# Copyright 2019 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base.fiscal import cnpj_cpf
    from erpbrasil.base.misc import punctuation_rm
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
    ]
    _nfe_search_keys = ["nfe40_CNPJ", "nfe40_CPF", "nfe40_xNome"]

    @api.model
    def _prepare_import_dict(self, values, model=None):
        values = super()._prepare_import_dict(values, model)
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
    nfe40_CEP = fields.Char(related="zip", readonly=False)
    nfe40_cPais = fields.Char(related="country_id.bc_code")
    nfe40_xPais = fields.Char(related="country_id.name")
    nfe40_fone = fields.Char(related="phone", readonly=False)  # TODO mobile?

    # nfe.40.dest
    nfe40_xNome = fields.Char(related="legal_name")
    nfe40_xFant = fields.Char(related="name")
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
            if rec.cnpj_cpf:
                if rec.country_id.code != "BR":
                    rec.nfe40_choice7 = "nfe40_idEstrangeiro"
                elif rec.is_company:
                    rec.nfe40_CNPJ = punctuation_rm(rec.cnpj_cpf)
                    rec.nfe40_choice7 = "nfe40_CNPJ"
                else:
                    rec.nfe40_CPF = punctuation_rm(rec.cnpj_cpf)
                    rec.nfe40_choice7 = "nfe40_CPF"

            if rec.inscr_est and rec.is_company:
                rec.nfe40_IE = punctuation_rm(rec.inscr_est)
            else:
                rec.nfe40_IE = None

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

    def _export_field(self, xsd_field, class_obj, member_spec):
        if xsd_field == "nfe40_xNome" and class_obj._name == "nfe.40.dest":
            if self.env.context.get("tpAmb") == "2":
                return "NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO " "- SEM VALOR FISCAL"
        if xsd_field == "nfe40_xBairro":
            if self.country_id.code != "BR":
                return "EX"

        if xsd_field == "nfe40_xMun":
            if self.country_id.code != "BR":
                return "EXTERIOR"

        if xsd_field == "nfe40_cMun":
            if self.country_id.code != "BR":
                return "9999999"

        if xsd_field == "nfe40_UF":
            if self.country_id.code != "BR":
                return "EX"
        if xsd_field == "nfe40_idEstrangeiro":
            if self.country_id.code != "BR":
                return self.vat or self.cnpj_cpf or self.rg or "EXTERIOR"
        return super()._export_field(xsd_field, class_obj, member_spec)

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        if model is None and 'nfe40_CNPJ' in rec_dict and 'nfe40_xNome' not in rec_dict and 'nfe40_CEP' in rec_dict:
            parent_domain = [('nfe40_CNPJ', '=', rec_dict.get('nfe40_CNPJ'))]
            parent_partner_match = self.search(parent_domain, limit=1)
            match = parent_partner_match.child_ids.filtered(lambda m: m.type == 'delivery')
            if match:
                if match.zip != rec_dict["nfe40_CEP"] or ('street_number' in rec_dict and match.street_number != rec_dict["street_number"]):
                    vals = {
                        'zip': rec_dict.get("zip"),
                        'street_name': rec_dict.get("street_name") if 'street_name' in rec_dict else False,
                        'street_number': rec_dict.get("street_number") if 'street_number' in rec_dict else False,
                        'street2': rec_dict.get("street2") if 'street2' in rec_dict else False,
                        'district': rec_dict.get("district") if 'district' in rec_dict else False,
                        'state_id': self.env['res.country.state'].search(
                            [('code', '=', rec_dict["nfe40_UF"]), ('country_id.bc_code', '=', rec_dict["nfe40_cPais"])],
                            limit=1).id if 'nfe40_UF' in rec_dict else False,
                        'city_id': self.env['res.city'].search([('ibge_code', '=', rec_dict["nfe40_cMun"])],
                                                               limit=1).id if 'nfe40_cMun' in rec_dict else False,
                        'country_id': self.env['res.country'].search([('bc_code', '=', rec_dict["nfe40_cPais"])],
                                                                     limit=1).id if 'nfe40_cPais' in rec_dict else False,
                    }
                    match.update(vals)
                return match.id
            vals = {
                'type': 'delivery',
                'parent_id': parent_partner_match.id,
                'company_type': 'person',
                'name': 'Endereço de entrega',
                'zip': rec_dict.get("zip"),
                'street_name': rec_dict.get("street_name") if 'street_name' in rec_dict else False,
                'street_number': rec_dict.get("street_number") if 'street_number' in rec_dict else False,
                'street2': rec_dict.get("street2") if 'street2' in rec_dict else False,
                'district': rec_dict.get("district") if 'district' in rec_dict else False,
                'email': rec_dict.get("email") if 'email' in rec_dict else False,
                'phone': rec_dict.get("phone") if 'phone' in rec_dict else False,
                'state_id': self.env['res.country.state'].search(
                    [('code', '=', rec_dict["nfe40_UF"]), ('country_id.bc_code', '=', rec_dict["nfe40_cPais"])],
                    limit=1).id if 'nfe40_UF' in rec_dict else False,
                'city_id': self.env['res.city'].search([('ibge_code', '=', rec_dict["nfe40_cMun"])],
                                                       limit=1).id if 'nfe40_cMun' in rec_dict else False,
                'country_id': self.env['res.country'].search([('bc_code', '=', rec_dict["nfe40_cPais"])],
                                                             limit=1).id if 'nfe40_cPais' in rec_dict else False,
            }
            delivery_adress = self.env['res.partner'].create(vals)
            parent_partner_match.child_ids.write({'child_ids': [(4, delivery_adress.id)]})
            return delivery_adress.id
        else:
            return super(ResPartner, self).match_or_create_m2o(rec_dict, parent_dict, model)
