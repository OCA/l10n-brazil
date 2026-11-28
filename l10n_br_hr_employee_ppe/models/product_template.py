# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    caepi_situacao = fields.Char(
        string="CA Status",
        compute="_compute_caepi_info",
        help="Status of the certificate of approval in the MTE database.",
    )
    caepi_equipamento = fields.Char(
        string="Equipment (MTE)",
        compute="_compute_caepi_info",
    )
    caepi_fabricante = fields.Char(
        string="Manufacturer (MTE)",
        compute="_compute_caepi_info",
    )

    @api.depends("ppe_certification")
    def _compute_caepi_info(self):
        Cert = self.env["caepi.certificate"]
        for rec in self:
            cert = Cert.lookup(rec.ppe_certification) if rec.ppe_certification else Cert
            rec.caepi_situacao = (
                dict(cert._fields["situacao"].selection).get(cert.situacao)
                if cert
                else False
            )
            rec.caepi_equipamento = cert.equipamento if cert else False
            rec.caepi_fabricante = cert.fabricante if cert else False

    @api.onchange("ppe_certification")
    def _onchange_ppe_certification_caepi(self):
        if not self.ppe_certification:
            return
        cert = self.env["caepi.certificate"].lookup(self.ppe_certification)
        if not cert:
            return {
                "warning": {
                    "title": _("CAEPI"),
                    "message": _(
                        "CA %(ca)s not found in the local MTE database. "
                        "Run the sync or check the number."
                    )
                    % {"ca": self.ppe_certification},
                }
            }
        self.ppe_certification_expiry_date = cert.data_validade
        if cert.situacao and cert.situacao != "valid":
            label = dict(cert._fields["situacao"].selection).get(
                cert.situacao, cert.situacao
            )
            return {
                "warning": {
                    "title": _("CAEPI — %(status)s") % {"status": label},
                    "message": _(
                        "CA %(ca)s has status «%(status)s» in the MTE database. "
                        "Expiry: %(expiry)s."
                    )
                    % {
                        "ca": self.ppe_certification,
                        "status": label,
                        "expiry": cert.data_validade or "—",
                    },
                }
            }
