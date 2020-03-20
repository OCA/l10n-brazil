# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import format_date

from ..constants.fiscal import (
    CERTIFICATE_SUBTYPE,
    CERTIFICATE_SUBTYPE_DEFAULT,
    CERTIFICATE_TYPE,
    CERTIFICATE_TYPE_DEFAULT)

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.assinatura import certificado
except ImportError:
    _logger.error(
        _("Python Library erpbrasil.assinatura not installed, "
          "please install ex: pip install erpbrasil.assinatura."))


class Certificate(models.Model):
    _name = "l10n_br_fiscal.certificate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Certificate"
    _order = "date_expiration"

    name = fields.Char(
        string="Name",
        compute="_compute_name",
        readonly=True)

    active = fields.Boolean(
        string="Active",
        default=True)

    date_start = fields.Datetime(
        string="Start Date",
        readonly=True,
        store=True)

    date_expiration = fields.Datetime(
        string="Expiration Date",
        readonly=True,
        store=True)

    issuer_name = fields.Char(
        string="Issuer",
        size=120,
        readonly=True,
        store=True)

    owner_name = fields.Char(
        string="Owner",
        size=120,
        readonly=True,
        store=True)

    owner_cnpj_cpf = fields.Char(
        string="CNPJ/CPF",
        size=18,
        readonly=True,
        store=True)

    type = fields.Selection(
        selection=CERTIFICATE_TYPE,
        string="Certificate Type",
        default=CERTIFICATE_TYPE_DEFAULT,
        required=True)

    subtype = fields.Selection(
        selection=CERTIFICATE_SUBTYPE,
        string="Document SubType",
        default=CERTIFICATE_SUBTYPE_DEFAULT,
        required=True)

    file = fields.Binary(
        string="file",
        prefetch=True,
        required=True)

    file_name = fields.Char(
        string="File Name",
        compute="_compute_description",
        size=255)

    password = fields.Char(
        string="Password",
        required=True)

    is_valid = fields.Boolean(
        compute="_compute_is_valid",
        string="Is Valid?",
        store=False)

    @api.model
    def _certificate_data(self, cert_file, cert_password):
        values = {}
        if cert_file and cert_password:
            try:
                cert = certificado.Certificado(
                    cert_file, cert_password)
            except Exception as e:
                raise ValidationError(
                    _("Cannot load Certificate ! \n\n {}".format(e)))

            if cert:
                values["issuer_name"] = cert.emissor
                values["owner_name"] = cert.proprietario
                values["owner_cnpj_cpf"] = cert.cnpj_cpf
                if cert.fim_validade:
                    values["date_expiration"] = cert.fim_validade.strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT
                    )

                if cert.inicio_validade:
                    values["date_start"] = cert.inicio_validade.strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT
                    )

        return values

    @api.multi
    @api.constrains("file", "password")
    def _check_certificate(self):
        for c in self:
            cert_values = c._certificate_data(c.file, c.password)
            if not cert_values:
                raise ValidationError(_("Cannot load Certificate !"))

    @api.depends("file", "password")
    def _compute_name(self):
        for c in self:
            if c.file and c.password:
                c.name = "{} - {} - {} - Valid: {}".format(
                    c.type and c.type.upper() or "",
                    c.subtype and c.subtype.upper() or "",
                    c.owner_name or "",
                    format_date(self.env, c.date_expiration),
                )

    @api.depends("date_expiration")
    def _compute_is_valid(self):
        for c in self:
            c.is_valid = False
            if c.date_expiration:
                c.is_valid = c.date_expiration >= fields.Datetime.now()

    @api.model
    def create(self, values):
        values.update(
            self._certificate_data(
                values.get("file"), values.get("password")))

        return super(Certificate, self).create(values)

    @api.multi
    def write(self, values):
        values.update(
            self._certificate_data(
                values.get("file"), values.get("password")))

        return super(Certificate, self).write(values)
