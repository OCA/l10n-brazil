# Copyright (C) 2019  Renato Lima - Akretion
# Copyright (C) 2024  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64
from contextlib import suppress

from cryptography import x509

from odoo import api, fields, models
from odoo.tools.misc import format_date

from ..constants import CERTIFICATE_SUBTYPE, CERTIFICATE_TYPE


class Certificate(models.Model):
    _inherit = "certificate.certificate"

    scope = fields.Selection(
        selection_add=[("l10n_br", "Brazilian Fiscal")],
    )

    type = fields.Selection(
        selection=CERTIFICATE_TYPE,
        string="Certificate Type",
    )

    subtype = fields.Selection(
        selection=CERTIFICATE_SUBTYPE,
        string="Document SubType",
    )

    name = fields.Char(
        compute="_compute_name",
        store=True,
    )

    owner_cnpj_cpf = fields.Char(
        string="CNPJ/CPF",
        compute="_compute_owner_cnpj_cpf",
        store=True,
    )

    issuer_name = fields.Char(
        string="Issuer",
        compute="_compute_issuer_name",
        store=True,
    )

    @api.depends("subject_common_name")
    def _compute_owner_cnpj_cpf(self):
        for certificate in self:
            cnpj_cpf = ""
            subject = certificate.subject_common_name or ""
            if ":" in subject:
                # Brazilian certificates carry the CNPJ/CPF in the subject CN
                # after the last colon, e.g. "NOME DA EMPRESA:12345678000190".
                cnpj_cpf = subject.rsplit(":", 1)[1]
            certificate.owner_cnpj_cpf = cnpj_cpf

    @api.depends("pem_certificate")
    def _compute_issuer_name(self):
        for certificate in self:
            issuer_name = ""
            pem_certificate = certificate.with_context(bin_size=False).pem_certificate
            if pem_certificate:
                with suppress(ValueError, TypeError):
                    x509_cert = x509.load_pem_x509_certificate(
                        base64.b64decode(pem_certificate)
                    )
                    issuer_name = self._get_common_name(x509_cert, issuer=True) or ""
            certificate.issuer_name = issuer_name

    @api.depends("type", "subtype", "subject_common_name", "date_end")
    def _compute_name(self):
        for certificate in self:
            parts = []
            if certificate.type:
                parts.append(certificate.type.upper())
            if certificate.subtype:
                parts.append(certificate.subtype.upper())
            if certificate.subject_common_name:
                parts.append(certificate.subject_common_name)
            if certificate.date_end:
                parts.append(
                    f"Valid: {format_date(self.env, certificate.date_end.date())}"
                )
            certificate.name = " - ".join(parts)
