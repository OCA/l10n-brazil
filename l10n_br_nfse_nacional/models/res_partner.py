# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class ResPartner(spec_models.SpecModel):
    _name = "res.partner"
    _inherit = [
        "res.partner",
        "nfse.10.tcinfopessoa",
        "nfse.10.tcendereco",
        "nfse.10.tcenderecosimples",
    ]

    _nfse10_binding_type_end = "Tcendereco"  # ", 'TcenderecoSimples', 'TcinfoPessoa'
    _nfse10_binding_type_toma = "TcinfoPessoa"  # ", 'TcenderecoSimples', 'TcinfoPessoa'

    nfse10_CNPJ = fields.Char(
        compute="_compute_nfse10_data", store=True, compute_sudo=True
    )
    nfse10_CPF = fields.Char(
        compute="_compute_nfse10_data", store=True, compute_sudo=True
    )
    nfse10_xNome = fields.Char(compute="_compute_nfse10_xNome")
    nfse10_IM = fields.Char(related="l10n_br_im_code")
    nfse10_email = fields.Char(related="email")
    nfse10_fone = fields.Char(
        compute="_compute_nfse10_data", store=True, compute_sudo=True
    )

    # Address mapping (from tcendereco / tcenderecosimples)
    nfse10_xLgr = fields.Char(related="street_name")
    nfse10_nro = fields.Char(related="street_number")
    nfse10_xCpl = fields.Char(related="street2")
    nfse10_xBairro = fields.Char(related="district")
    nfse10_cMun = fields.Char(related="city_id.ibge_code")
    nfse10_CEP = fields.Char(
        compute="_compute_nfse10_data", store=True, compute_sudo=True
    )

    nfse10_end = fields.Many2one("res.partner", compute="_compute_nfse10_end")
    nfse10_endNac = fields.Many2one("res.partner", compute="_compute_nfse10_end")
    nfse10_cNaoNIF = fields.Selection(compute="_compute_nfse10_cNaoNIF")

    @api.depends("is_company", "cnpj_cpf_stripped", "zip", "phone")
    def _compute_nfse10_data(self):
        for rec in self:
            if rec.cnpj_cpf_stripped:
                if rec.is_company:
                    rec.nfse10_CNPJ = rec.cnpj_cpf_stripped
                    rec.nfse10_CPF = False
                else:
                    rec.nfse10_CNPJ = False
                    rec.nfse10_CPF = rec.cnpj_cpf_stripped
            else:
                rec.nfse10_CNPJ = False
                rec.nfse10_CPF = False

            rec.nfse10_CEP = punctuation_rm(rec.zip)
            rec.nfse10_fone = punctuation_rm(rec.phone or "").replace(" ", "")

    @api.depends("legal_name", "name")
    def _compute_nfse10_xNome(self):
        for rec in self:
            rec.nfse10_xNome = rec.legal_name or rec.name

    def _compute_nfse10_end(self):
        for rec in self:
            rec.nfse10_end = rec.id
            rec.nfse10_endNac = rec.id

    @api.depends("country_id", "cnpj_cpf_stripped")
    def _compute_nfse10_cNaoNIF(self):
        for rec in self:
            if (
                rec.cnpj_cpf_stripped
                or not rec.country_id
                or rec.country_id.code == "BR"
            ):
                rec.nfse10_cNaoNIF = False
            else:
                rec.nfse10_cNaoNIF = "1"  # 1 - Dispensado do NIF

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        if field_name in ("nfse10_end", "nfse10_endNac"):
            # Extract flattened address fields from self when exporting <end>
            return self._build_binding(
                class_name=class_obj._fields[field_name].comodel_name,
                field_name=field_name,
            )
        return super()._export_many2one(field_name, xsd_required, class_obj)
