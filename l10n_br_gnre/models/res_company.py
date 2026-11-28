# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

GNRE_ENVIRONMENTS = [
    ("1", "Produção"),
    ("2", "Homologação"),
]


class ResCompany(models.Model):
    _inherit = "res.company"

    gnre_environment = fields.Selection(
        selection=GNRE_ENVIRONMENTS,
        string="Ambiente da GNRE",
        default="2",
        help="Portal GNRE de testes (homologação) ou de produção.",
    )

    def _gnre_certificate(self):
        """PKCS12 bytes and password of the company certificate."""
        self.ensure_one()
        certificate = self.certificate.sudo().with_context(bin_size=False)
        return certificate.file, certificate.password

    def _gnre_client(self):
        """Return the nfelib GNRE client with the company certificate."""
        from nfelib.gnre.client.v2_0 import GnreClient

        self.ensure_one()
        pkcs12_data, pkcs12_password = self._gnre_certificate()
        return GnreClient(
            ambiente=self.gnre_environment,
            pkcs12_data=pkcs12_data,
            pkcs12_password=pkcs12_password,
        )
