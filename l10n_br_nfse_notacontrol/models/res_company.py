# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

try:
    from erpbrasil.edoc.provedores.notacontrol import MUNICIPIOS
except ImportError:  # pragma: no cover - lib ausente
    MUNICIPIOS = {}


class ResCompany(models.Model):
    _inherit = "res.company"

    nfse_notacontrol = fields.Boolean(
        string="NFS-e via NotaControl",
        compute="_compute_nfse_notacontrol",
        help="The company city receives the national DPS through the "
        "NotaControl municipal webservice instead of the ADN.",
    )
    nfse_notacontrol_algorithm = fields.Selection(
        selection=[("sha1", "RSA-SHA1"), ("sha256", "RSA-SHA256")],
        string="NotaControl Signature",
        default="sha1",
        help="The official NotaControl batch sample signs with RSA-SHA1; "
        "switch to SHA256 if the webservice rejects the signature (E0714).",
    )
    nfse_notacontrol_simulated = fields.Boolean(
        string="Simulate NotaControl",
        help="Demo/rehearsal only: the DPS is signed and packed exactly as it "
        "would be sent, but nothing is transmitted and an authorization is "
        "simulated. Every document touched is flagged as SIMULATED.",
    )

    def _compute_nfse_notacontrol(self):
        for company in self:
            ibge = company.city_id.ibge_code or ""
            company.nfse_notacontrol = ibge.isdigit() and int(ibge) in MUNICIPIOS
