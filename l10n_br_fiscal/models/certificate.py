# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from ..constants.fiscal import (
    CERTIFICATE_TYPE,
    CERTIFICATE_TYPE_DEFAULT,
    CERTIFICATE_SUBTYPE,
    CERTIFICATE_SUBTYPE_DEFAULT
)


class Certificate(models.Model):
    _name = 'fiscal.certificate'
    _description = 'Certificate'
    _order = 'date_expiration desc'

    name = fields.Char(
        string='Name',
        compute='_compute_description',
        store=False)

    date_expiration = fields.Datetime(
        string='Expiration Date')

    owner_name = fields.Char(
        string='Owner',
        size=120)

    owner_cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        size=18)

    type = fields.Selection(
        selection=CERTIFICATE_TYPE,
        string='Certificate Type',
        default=CERTIFICATE_TYPE_DEFAULT,
        required=True)

    subtype = fields.Selection(
        selection=CERTIFICATE_SUBTYPE,
        string='Document SubType',
        default=CERTIFICATE_SUBTYPE_DEFAULT,
        required=True)

    file = fields.Binary(
        string='file',
        attachment=True,
        required=True)

    file_name = fields.Char(
        string='File Name',
        compute='_compute_description',
        size=255)

    password = fields.Char(
        string='Password')

    is_valid = fields.Boolean(
        compute='_compute_is_valid',
        string='Is Valid?',
        store=False)

    @api.multi
    @api.constrains('file', 'password')
    def _check_certificate(self):
        for record in self:
            domain = []

            if not record.file and not record.password:
                return

            try:
                cert = certificate.check_password(certificate.file,
                                                  certificate.password)
            except:
                raise ValidationError(_('Cannot load Certificate !'))

    @api.depends('type', 'subtype', 'owner_name',
                 'owner_cnpj_cpf', 'date_expiration', 'file')
    def _compute_description(self):
        for c in self:
            description = "{0} - {1} - {2} - Valid: {3}".format(
                c.type and c.type.upper() or '',
                c.subtype and c.subtype.upper() or '',
                # TODO Format CNPJ/CPF
                c.owner_cnpj_cpf and c.owner_cnpj_cpf.upper() or '',
                # TODO Fromat date
                c.date_expiration or '')

    @api.depends('date_expiration')
    def _compute_is_valid(self):
        for record in self:
            record.is_valid = False
            if record.date_expiration:
                record.is_valid = record.date_expiration <= str(
                    fields.datetime.now())

    @api.onchange('file', 'password')
    def _onchange_file(self):
        #TODO - Get data from Certificate
        # for record in self:
        #     record._check_certificate()
        #     cert = certificate.get_info(record.file,
        #                                 record.password)
        #
        #     record.type = cert.Type
        #     record.subtype = cert.subtype
        #     record.subtype = cert.subtype
        #     record.owner_name = cert.owner_name
        #     record.owner_cnpj_cpf = cert.owner_cnpj_cpf
        #     record.date_expiration = cert.date_expiration
        pass
