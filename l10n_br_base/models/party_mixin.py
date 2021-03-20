# Copyright (C) 2021 Renato Lima (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base.fiscal import cnpj_cpf
    from erpbrasil.base import misc
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class PartyMixin(models.AbstractModel):
    _name = "l10n_br_base.party.mixin"
    _description = "Brazilian partner and company data mixin"

    cnpj_cpf = fields.Char(
        string="CNPJ/CPF",
        size=18,
    )

    inscr_est = fields.Char(
        string="State Tax Number/RG",
        size=17,
    )

    state_tax_number_ids = fields.One2many(
        string="Others State Tax Number",
        comodel_name="state.tax.numbers",
        inverse_name="partner_id",
        ondelete="cascade",
    )

    inscr_mun = fields.Char(
        string="Municipal Tax Number",
        size=18,
    )

    suframa = fields.Char(
        string="Suframa",
        size=18,
    )

    legal_name = fields.Char(
        string="Legal Name",
        size=128,
        help="Used in fiscal documents",
    )

    city_id = fields.Many2one(
        string="City of Address",
        comodel_name="res.city",
        domain="[('state_id', '=', state_id)]",
    )

    country_id = fields.Many2one(
        comodel_name="res.country.state",
        default=lambda self: self.env.ref("base.br"),
    )

    district = fields.Char(
        string="District",
        size=32,
    )

    @api.onchange("cnpj_cpf")
    def _onchange_cnpj_cpf(self):
        self.cnpj_cpf = cnpj_cpf.formata(str(self.cnpj_cpf))

    @api.onchange("zip")
    def _onchange_zip(self):
        self.zip = misc.format_zipcode(self.zip, self.country_id.code)

    @api.onchange("state_id")
    def _onchange_state(self):
        self.city_id = None

    @api.onchange("city_id")
    def _onchange_city_id(self):
        self.city = self.city_id.name
