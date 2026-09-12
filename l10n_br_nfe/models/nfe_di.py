# Copyright 2021 Akretion (Renato Lima <renato.lima@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm

from odoo import api, fields, models

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
        string="State Customs Clearance",
        domain=[("country_id.code", "=", "BR")],
    )

    nfe40_UFDesemb = fields.Selection(
        compute="_compute_nfe40_UFDesemb",
        inverse="_inverse_nfe40_UFDesemb",
        string="Customs Clearance Code",
    )

    @api.depends("state_clearance_id")
    def _compute_nfe40_UFDesemb(self):
        for record in self:
            record.nfe40_UFDesemb = record.state_clearance_id.code

    def _inverse_nfe40_UFDesemb(self):
        state_model = self.env["res.country.state"]
        for record in self:
            record.state_clearance_id = record.nfe40_UFDesemb and state_model.search(
                [
                    ("country_id.code", "=", "BR"),
                    ("code", "=", record.nfe40_UFDesemb),
                ],
                limit=1,
            )

    nfe40_tpViaTransp = fields.Selection(
        selection=TPVIATRANSP_DI,
    )

    nfe40_tpIntermedio = fields.Selection(
        selection=TPINTERMEDIO_DI,
    )

    partner_acquirer_id = fields.Many2one(
        comodel_name="res.partner", string="Partner Acquirer"
    )

    nfe40_CNPJ = fields.Char(
        compute="_compute_nfe40_acquirer",
        inverse="_inverse_nfe40_acquirer",
    )

    nfe40_UFTerceiro = fields.Selection(
        compute="_compute_nfe40_acquirer",
        inverse="_inverse_nfe40_acquirer",
    )

    @api.depends("partner_acquirer_id")
    def _compute_nfe40_acquirer(self):
        for record in self:
            record.nfe40_CNPJ = record.partner_acquirer_id.nfe40_CNPJ
            record.nfe40_UFTerceiro = record.partner_acquirer_id.state_id.code

    def _inverse_nfe40_acquirer(self):
        partner_model = self.env["res.partner"]
        state_model = self.env["res.country.state"]
        for record in self:
            if record.nfe40_CNPJ and not record.partner_acquirer_id:
                stripped = punctuation_rm(record.nfe40_CNPJ)
                record.partner_acquirer_id = partner_model.search(
                    ["|", ("cnpj_cpf_stripped", "=", stripped), ("vat", "=", stripped)],
                    limit=1,
                ) or partner_model.create(
                    {
                        "name": f"contato CNPJ {record.nfe40_CNPJ}",
                        "is_company": True,
                        "vat": stripped,
                    }
                )
            if record.nfe40_UFTerceiro and not record.partner_acquirer_id.state_id:
                record.partner_acquirer_id.state_id = state_model.search(
                    [
                        ("country_id.code", "=", "BR"),
                        ("code", "=", record.nfe40_UFTerceiro),
                    ],
                    limit=1,
                )
