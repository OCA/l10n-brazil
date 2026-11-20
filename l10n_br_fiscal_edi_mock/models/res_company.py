# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    edoc_mock_mode = fields.Boolean(
        string="SEFAZ simulada (emissao)",
        help="Quando marcado, a autorizacao, o cancelamento e a carta de "
        "correcao de NF-e, NFC-e, CT-e e MDF-e sao respondidos por um "
        "simulador local, sem comunicacao com a SEFAZ. So funciona em "
        "ambiente de homologacao.",
    )
