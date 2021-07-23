# Copyright 2021 Akretion (Renato Lima <renato.lima@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

TPVIATRANSP_DI = [
    ("1", "1 - Maritima"),
    ("2", "2 - Fluvial"),
    ("3", "3 - Lacustre"),
    ("4", "4 - Aerea"),
    ("5", "5 - Postal"),
    ("6", "6 - Ferroviaria"),
    ("7", "7 - Rodoviaria"),
    ("8", "8 - Conduto/Rede Transmissão"),
    ("9", "9 - Meios Próprios"),
    ("10", "10 - Entrada/Saída Ficta"),
    ("11", "11 - Courier"),
    ("12", "12 - Em mãos"),
    ("13", "13 - Por reboque"),
]

TPINTERMEDIO_DI = [
    ("1", "1 - Por conta própria"),
    ("2", "2 - Por conta e ordem"),
    ("3", "3 - Encomenda"),
]


class NFeDI(models.AbstractModel):
    _inherit = "nfe.40.di"

    state_clearance_id = fields.Many2one(
        comodel_name="res.country.state",
        string="State Clearance",
    )

    nfe40_UFDesemb = fields.Char(
        related="state_clearance_id.code",
    )

    nfe40_tpViaTransp = fields.Selection(
        selection=TPVIATRANSP_DI,
    )

    nfe40_tpIntermedio = fields.Selection(
        selection=TPINTERMEDIO_DI,
    )

    partner_acquirer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner Acquirer"
    )

    nfe40_CNPJ = fields.Char(
        related="partner_acquirer_id.nfe40_CNPJ",
    )

    nfe40_UFTerceiro = fields.Char(
        related="partner_acquirer_id.state_id.code",
    )
