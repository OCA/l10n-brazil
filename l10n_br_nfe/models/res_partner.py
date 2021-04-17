# Copyright 2019 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class ResPartner(spec_models.SpecModel):
    # NOTE TODO
    # dest has a m2o tendereco. tlocal and tendereco are really similar...
    # what happen to m2o to tendereco if we don't inherit from tendereco?
    # should we stack tendereco from dest? will m2o to tendereco work?
    # can we use related fields and context views to avoid troubles?
    _name = 'res.partner'
    _inherit = ['res.partner', 'nfe.40.tendereco',
                'nfe.40.tlocal', 'nfe.40.dest', 'nfe.40.tenderemi',
                'nfe.40.tinfresptec']
    _nfe_search_keys = ['nfe40_CNPJ', 'nfe40_CPF', 'nfe40_xNome']

    @api.model
    def _prepare_import_dict(self, values, model=None):
        values = super()._prepare_import_dict(values, model)
        if not values.get('name') and values.get('legal_name'):
            values['name'] = values['legal_name']
        return values

    # nfe.40.tlocal / nfe.40.enderEmit / 'nfe.40.enderDest
    # TODO: may be not store=True -> then override match
    nfe40_CNPJ = fields.Char(compute='_compute_nfe_data',
                             inverse='_inverse_nfe40_CNPJ',
                             store=True)
    nfe40_CPF = fields.Char(compute='_compute_nfe_data',
                            inverse='_inverse_nfe40_CNPJ',
                            store=True)
    nfe40_xLgr = fields.Char(related='street', readonly=False)
    nfe40_nro = fields.Char(related='street_number', readonly=False)
    nfe40_xCpl = fields.Char(related='street2', readonly=False)
    nfe40_xBairro = fields.Char(related='district', readonly=False)
    nfe40_cMun = fields.Char(compute='_compute_nfe_data',
                             inverse='_inverse_nfe40_cMun')
    nfe40_xMun = fields.Char(related='city_id.name')
    # Char overriding Selection:
    nfe40_UF = fields.Char(related='state_id.code')

    # nfe.40.tendereco
    nfe40_CEP = fields.Char(related='zip', readonly=False)
    nfe40_cPais = fields.Char(related='country_id.bc_code')
    nfe40_xPais = fields.Char(related='country_id.name')
    nfe40_fone = fields.Char(related='phone', readonly=False)  # TODO mobile?

    # nfe.40.dest
#    nfe40_idEstrangeiro = fields.Char(
    nfe40_xNome = fields.Char(related='legal_name')
    nfe40_enderDest = fields.Many2one('res.partner',
                                      compute='_compute_nfe40_enderDest')
    nfe40_indIEDest = fields.Selection(related='ind_ie_dest')
    nfe40_IE = fields.Char(related='inscr_est')
    nfe40_ISUF = fields.Char(related='suframa')
    nfe40_email = fields.Char(related='email')

    # nfe.40.infresptec
    nfe40_xContato = fields.Char(related='legal_name')

    nfe40_choice2 = fields.Selection([
        ('nfe40_CNPJ', 'CNPJ'),
        ('nfe40_CPF', 'CPF')],
        "CNPJ/CPF do Parceiro")

    @api.multi
    def _compute_nfe40_enderDest(self):
        for rec in self:
            rec.nfe40_enderDest = rec.id

    @api.multi
    def _compute_nfe_data(self):
        """Set schema data which are not just related fields"""
        for rec in self:
            if rec.cnpj_cpf:
                if rec.is_company:
                    rec.nfe40_CNPJ = rec.cnpj_cpf
                else:
                    rec.nfe40_CPF = rec.cnpj_cpf
            rec.nfe40_cMun = "%s%s" % (rec.state_id.ibge_code,
                                       rec.city_id.ibge_code)

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

    def _inverse_nfe40_cMun(self):
        for rec in self:
            if self.nfe40_cMun and len(self.nfe40_cMun) == 7:
                state_ibge = self.nfe40_cMun[0:1]
                city_ibge = self.nfe40_cMun[2:8]
                state = self.env['res.country.state'].search(
                    [('ibge_code', '=', state_ibge)], limit=1)
                rec.state_id = state.id
                city = self.env['res.city'].search(
                    [('ibge_code', '=', city_ibge)], limit=1)
                rec.city_id = city.id

    def _export_field(self, xsd_field, class_obj, member_spec):
        if xsd_field == 'nfe40_xNome' and class_obj._name == 'nfe.40.dest':
            if self.env.context.get('tpAmb') == '2':
                return 'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO ' \
                       '- SEM VALOR FISCAL'
        return super()._export_field(xsd_field, class_obj, member_spec)
