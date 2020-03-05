# Copyright 2019 Akretion
# Copyright 2019 KMEE INFORMATICA LTDA

from odoo import api, fields
from odoo.addons.spec_driven_model.models import spec_models
from erpbrasil.base import misc


class ResPartner(spec_models.SpecModel):
    # NOTE TODO
    # dest has a m2o tendereco. tlocal and tendereco are really similar...
    # what happen to m2o to tendereco if we don't inherit from tendereco?
    # should we stack tendereco from dest? will m2o to tendereco work?
    # can we use related fields and context views to avoid troubles?
    _inherit = ["res.partner", "nfe.40.tendereco", "nfe.40.tenderemi",
                "nfe.40.tlocal", "nfe.40.dest"]
    _name = "res.partner"
    _nfe_search_keys = ['nfe40_CNPJ', 'nfe40_CPF', 'nfe40_xNome']

    @api.model
    def _prepare_import_dict(self, vals, defaults=False):
        vals = super(ResPartner, self)._prepare_import_dict(vals, defaults)
        if not vals.get('name') and vals.get('legal_name'):
            vals['name'] = vals['legal_name']
        return vals

    # TODO deal with nfe40_enderDest. Item can be the address with dest on the
    #  parent...

    # nfe.40.tlocal
    nfe40_CNPJ = fields.Char(compute='_compute_nfe_data',
                             inverse='_inverse_nfe40_CNPJ',
                             store=True)
    # TODO may be not store=True -> then override match
    nfe40_CPF = fields.Char(compute='_compute_nfe_data',
                            inverse='_inverse_nfe40_CNPJ',
                            store=True)
    nfe40_xLgr = fields.Char(related='street')
    nfe40_nro = fields.Char(related='street_number')
    nfe40_xCpl = fields.Char(related='street2')
    nfe40_xBairro = fields.Char(related='district')
    nfe40_cMun = fields.Char(compute='_compute_nfe_data',
                             inverse='_inverse_nfe40_cMun')
    nfe40_xMun = fields.Char(related='city_id.name')
    # Char overriding Selection:
    nfe40_UF = fields.Char(related='state_id.code')

    # nfe.40.tendereco
    nfe40_CEP = fields.Char(
        compute='_compute_nfe_data',
        nverse='_inverse_nfe40_zip'
    )
    nfe40_cPais = fields.Char(related='country_id.ibge_code')
    nfe40_xPais = fields.Char(related='country_id.name')
    nfe40_fone = fields.Char(
        compute='_compute_nfe_data',
        inverse='_inverse_nfe40_phone'
    )  # TODO or mobile?

    # nfe.40.dest
    #    nfe40_idEstrangeiro = fields.Char(
    nfe40_xNome = fields.Char(related='legal_name')
    #    nfe40_enderDest = fields.Many2one TODO
    #    nfe40_IE = fields.Char(related='') TODO
    nfe40_ISUF = fields.Char(related='suframa')
    nfe40_email = fields.Char(related='email')

    @api.multi
    def _compute_nfe_data(self):
        """Set schema data which are not just related fields"""
        for rec in self:
            if rec.cnpj_cpf:
                if rec.is_company:
                    rec.nfe40_CNPJ = misc.punctuation_rm(rec.cnpj_cpf)
                else:
                    rec.nfe40_CPF = misc.punctuation_rm(rec.cnpj_cpf)
            rec.nfe40_cMun = "%s%s" % (rec.state_id.ibge_code,
                                       rec.city_id.ibge_code)
            if rec.zip:
                rec.nfe40_CEP = misc.punctuation_rm(rec.zip)

            if rec.phone:
                rec.nfe40_fone = misc.punctuation_rm(rec.phone).replace(" ", "")

    def _inverse_nfe40_CNPJ(self):
        for rec in self:
            if rec.nfe40_CNPJ:
                rec.is_company = True
                rec.cnpj_cpf = rec.nfe40_CNPJ

    def _inverse_nfe40_CPF(self):
        for rec in self:
            if rec.nfe40_CPF:
                rec.is_company = False
                rec.cnpj_cpf = rec.nfe40_CPF

    def _inverse_nfe40_zip(self):
        for rec in self:
            if rec.nfe40_ZIP:
                rec.zip = rec.nfe40_ZIP

    def _inverse_nfe40_cMun(self):
        for rec in self:
            if len(self.nfe40_cMun) == 7:
                state_ibge = self.nfe40_cMun[0:1]
                city_ibge = self.nfe40_cMun[2:8]
                state = self.env['res.country.state'].search(
                    [('ibge_code', '=', state_ibge)], limit=1)
                rec.state_id = state.id
                city = self.env['res.city'].search(
                    [('ibge_code', '=', city_ibge)], limit=1)
                rec.city_id = city.id

    def _inverse_nfe40_phone(self):
        for rec in self:
            if rec.nfe40_fone:
                rec.phone = rec.nfe40_fone
