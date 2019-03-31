# Copyright (C) 2009 Gabriel C. Stabel
# Copyright (C) 2009 Renato Lima (Akretion)
# Copyright (C) 2012 Raphaël Valyi (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from ..tools import fiscal, misc


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _display_address(self, without_company=False):
        country_code = self.country_id.code or ''
        if self.country_id and country_code.upper() != 'BR':
            # this ensure other localizations could do what they want
            return super(Partner, self)._display_address(
                without_company=False)
        else:
            address_format = (
                self.country_id and self.country_id.address_format or
                "%(street)s, %(street_number)s\n%(street2)s\n%(city)s"
                " %(state_code)s%(zip)s\n%(country_name)s")
            args = {
                'state_code': self.state_id and self.state_id.code or '',
                'state_name': self.state_id and self.state_id.name or '',
                'country_code': self.country_id and self.country_id.code or '',
                'country_name': self.country_id and self.country_id.name or '',
                'company_name': self.parent_id and self.parent_id.name or ''}

            address_field = ['title', 'street', 'street2', 'zip',
                             'city', 'street_number', 'district']
            for field in address_field:
                args[field] = getattr(self, field) or ''
            if without_company:
                args['company_name'] = ''
            elif self.parent_id:
                address_format = '%(company_name)s\n' + address_format
            return address_format % args

    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        size=18)

    inscr_est = fields.Char(
        string='State Tax Number/RG',
        size=16)

    state_tax_number_ids = fields.One2many(
        string='Others State Tax Number',
        comodel_name='state.tax.numbers',
        inverse_name='partner_id',
        ondelete='cascade')

    inscr_mun = fields.Char(
        string='Municipal Tax Number',
        size=18)

    suframa = fields.Char(
        string='Suframa',
        size=18)

    legal_name = fields.Char(
        string='Legal Name',
        size=128,
        help="Used in fiscal documents")

    city_id = fields.Many2one(
        domain="[('state_id', '=', state_id)]")

    country_id = fields.Many2one(
        default=lambda self: self.env.ref('base.br'))

    district = fields.Char(
        string='District',
        size=32)

    union_entity_code = fields.Char(
        string='Union Entity code')

    @api.multi
    @api.constrains('cnpj_cpf', 'inscr_est')
    def _check_cnpj_inscr_est(self):
        for record in self:
            domain = []

            # permite cnpj vazio
            if not record.cnpj_cpf:
                return

            allow_cnpj_multi_ie = record.env['ir.config_parameter'].get_param(
                'l10n_br_base_allow_cnpj_multi_ie', default=True)

            if record.parent_id:
                domain += [
                    ('id', 'not in', record.parent_id.ids),
                    ('parent_id', 'not in', record.parent_id.ids)
                ]

            domain += [
                ('cnpj_cpf', '=', record.cnpj_cpf),
                ('id', '!=', record.id)
            ]

            # se encontrar CNPJ iguais
            if record.env['res.partner'].search(domain):

                if allow_cnpj_multi_ie == 'True':
                    for partner in record.env['res.partner'].search(domain):
                        if (partner.inscr_est == record.inscr_est and
                                not record.inscr_est):
                            raise ValidationError(_(
                                'There is already a partner record with this'
                                'Estadual Inscription !'))
                else:
                    raise ValidationError(_(
                        'There is already a partner record with this CNPJ !'))

    @api.multi
    @api.constrains('cnpj_cpf', 'country_id')
    def _check_cnpj_cpf(self):
        result = True
        for record in self:
            country_code = record.country_id.code or ''
            if record.cnpj_cpf and country_code.upper() == 'BR':
                if record.is_company:
                    if not fiscal.validate_cnpj(record.cnpj_cpf):
                        result = False
                        document = 'CNPJ'
                elif not fiscal.validate_cpf(record.cnpj_cpf):
                    result = False
                    document = 'CPF'
            if not result:
                raise ValidationError(_("{} Invalid!").format(document))

    @api.multi
    @api.constrains('inscr_est', 'state_id')
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False.

        :Parameters:
        """
        for record in self:
            result = True
            if record.inscr_est and record.is_company and record.state_id:
                state_code = record.state_id.code or ''
                uf = state_code.lower()
                result = fiscal.validate_ie(uf, record.inscr_est)
            if not result:
                raise ValidationError(_("Estadual Inscription Invalid !"))

    @api.multi
    @api.constrains('state_tax_number_ids')
    def _check_state_tax_number_ids(self):
        """Checks if field other insc_est is valid,
        this method call others methods because this validation is State wise
        :Return: True or False.
        """
        for record in self:
            for inscr_est_line in record.state_tax_number_ids:
                state_code = inscr_est_line.state_id.code or ''
                uf = state_code.lower()
                valid_ie = fiscal.validate_ie(uf, inscr_est_line.inscr_est)
                if not valid_ie:
                    raise ValidationError(_('Invalid State Tax Number!'))
                if inscr_est_line.state_id.id == record.state_id.id:
                    raise ValidationError(_(
                        'There can only be one state tax'
                        ' number per state for each partner!'))
                duplicate_ie = record.search([
                    ('state_id', '=', inscr_est_line.state_id.id),
                    ('inscr_est', '=', inscr_est_line.inscr_est)
                ])
                if duplicate_ie:
                    raise ValidationError(_(
                        'State Registration already used'
                        ' %s' % duplicate_ie.name))

    @api.model
    def _address_fields(self):
        """Returns the list of address
        fields that are synced from the parent."""
        return super(Partner, self)._address_fields() + ['district']

    def get_street_fields(self):
        """Returns the fields that can be used in a street format.
        Overwrite this function if you want to add your own fields."""
        return super(Partner, self).get_street_fields() + ('street',)

    @api.onchange('cnpj_cpf', 'country_id')
    def _onchange_cnpj_cpf(self):
        country = self.country_id.code or ''
        self.cnpj_cpf = fiscal.format_cpf_cnpj(self.cnpj_cpf,
                                               country,
                                               self.is_company)

    @api.onchange('zip')
    def _onchange_zip(self):
        self.zip = misc.format_zipcode(self.zip,
                                       self.country_id.code)

    @api.onchange('city_id')
    def _onchange_city_id(self):
        self.city = self.city_id.name
