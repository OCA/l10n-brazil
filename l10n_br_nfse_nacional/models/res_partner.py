from erpbrasil.base.misc import punctuation_rm
from odoo import fields, api
from odoo.addons.spec_driven_model.models import spec_models

class ResPartner(spec_models.SpecModel):
    _name = "res.partner"
    _inherit = [
        "res.partner",
        "nfse.10.tcinfopessoa",
        "nfse.10.tcendereco",
        "nfse.10.tcenderecosimples",
    ]

    _nfse10_binding_type_end = "Tcendereco" #", 'TcenderecoSimples', 'TcinfoPessoa'
    _nfse10_binding_type_toma = "TcinfoPessoa" #", 'TcenderecoSimples', 'TcinfoPessoa'

    nfse10_CNPJ = fields.Char(compute="_compute_nfse10_data", store=True, compute_sudo=True)
    nfse10_CPF = fields.Char(compute="_compute_nfse10_data", store=True, compute_sudo=True)
    nfse10_xNome = fields.Char(related="legal_name")
    nfse10_IM = fields.Char(related="l10n_br_im_code")
    nfse10_email = fields.Char(related="email")
    nfse10_fone = fields.Char(compute="_compute_nfse10_data", store=True, compute_sudo=True)

    # Address mapping (from tcendereco / tcenderecosimples)
    nfse10_xLgr = fields.Char(related="street_name")
    nfse10_nro = fields.Char(related="street_number")
    nfse10_xCpl = fields.Char(related="street2")
    nfse10_xBairro = fields.Char(related="district")
    nfse10_cMun = fields.Char(related="city_id.ibge_code")
    nfse10_CEP = fields.Char(compute="_compute_nfse10_data", store=True, compute_sudo=True)

    nfse10_end = fields.Many2one("res.partner", compute="_compute_nfse10_end")
    nfse10_cNaoNIF = fields.Selection(compute="_compute_nfse10_cNaoNIF")

    @api.depends("is_company", "cnpj_cpf", "zip", "phone")
    def _compute_nfse10_data(self):
        for rec in self:
            cnpj_cpf_stripped = punctuation_rm(rec.cnpj_cpf)
            if cnpj_cpf_stripped:
                if rec.is_company:
                    rec.nfse10_CNPJ = cnpj_cpf_stripped
                    rec.nfse10_CPF = False
                else:
                    rec.nfse10_CNPJ = False
                    rec.nfse10_CPF = cnpj_cpf_stripped
            else:
                rec.nfse10_CNPJ = False
                rec.nfse10_CPF = False

            rec.nfse10_CEP = punctuation_rm(rec.zip)
            rec.nfse10_fone = punctuation_rm(rec.phone or "").replace(" ", "")

    def _compute_nfse10_end(self):
        for rec in self:
            rec.nfse10_end = rec.id

    @api.depends("country_id")
    def _compute_nfse10_cNaoNIF(self):
        for rec in self:
            if rec.country_id and rec.country_id.code != "BR":
                rec.nfse10_cNaoNIF = "1"  # 1 - Dispensado do NIF
            else:
                rec.nfse10_cNaoNIF = "0"  # 0 - Não informado na nota de origem

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        if field_name == "nfse10_end":
            # Extract flattened address fields from self when exporting <end>
            return self._build_binding(class_name=class_obj._fields[field_name].comodel_name, field_name=field_name)
        return super()._export_many2one(field_name, xsd_required, class_obj)
