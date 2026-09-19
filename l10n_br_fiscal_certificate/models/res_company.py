# Copyright (C) 2013  Renato Lima - Akretion
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re

from erpbrasil.assinatura import certificado as cert

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_date


class ResCompany(models.Model):
    _inherit = "res.company"

    certificate_id = fields.Many2one(
        comodel_name="certificate.certificate",
        string="Certificate",
        domain="[('company_id', '=', id), ('scope', '=', 'l10n_br')]",
        help="Certificate used to sign and transmit the fiscal documents.",
    )

    certificate = fields.Many2one(
        comodel_name="certificate.certificate",
        compute="_compute_certificate",
    )

    @api.depends("certificate_id")
    def _compute_certificate(self):
        for record in self:
            record.certificate = record.sudo().certificate_id

    def _get_br_certificate(self, only_ecnpj=False):
        """Return the certificate to sign and transmit the fiscal documents of
        the company, as superuser: the users don't need to read it."""
        self.ensure_one()
        certificate = self.sudo().certificate
        if not certificate:
            raise ValidationError(
                _("No certificate set for the company %s.", self.display_name)
            )
        if not certificate.is_valid:
            raise ValidationError(
                _(
                    "The certificate of the company %(company)s is not valid "
                    "(validity: %(start)s to %(end)s).",
                    company=self.display_name,
                    start=format_date(self.env, certificate.date_start),
                    end=format_date(self.env, certificate.date_end),
                )
            )
        if (
            only_ecnpj
            and len(re.sub(r"\D", "", certificate.owner_cnpj_cpf or "")) != 14
        ):
            raise ValidationError(
                _("Only an e-CNPJ certificate can be used for this operation.")
            )
        return certificate

    def _get_br_ecertificate(self, only_ecnpj=False):
        certificate = self._get_br_certificate(only_ecnpj=only_ecnpj)
        return cert.Certificado(
            arquivo=certificate.with_context(bin_size=False).content,
            senha=certificate.pkcs12_password,
        )
