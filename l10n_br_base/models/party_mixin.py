# Copyright (C) 2021 Renato Lima (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re

from erpbrasil.base import misc
from erpbrasil.base.fiscal import cnpj_cpf

from odoo import api, fields, models


class PartyMixin(models.AbstractModel):
    _name = "l10n_br_base.party.mixin"
    _description = "Brazilian partner and company data mixin"

    # this cnpj_cpf field helps maintaining the compatibility with the legacy codebase
    # while using the vat field for CNPJ and l10n_br_cpf_code for CPF as Odoo SA did.
    cnpj_cpf = fields.Char(
        string="CNPJ/CPF",
        inverse="_inverse_cnpj_cpf",
        compute="_compute_cnpj_cpf",
    )

    cnpj_cpf_stripped = fields.Char(
        string="CNPJ/CPF Stripped",
        help="CNPJ/CPF without special characters",
        compute="_compute_cnpj_cpf_stripped",
        store=True,
        index=True,
    )

    l10n_br_cpf_code = fields.Char(string="CPF", help="Natural Persons Register")

    inscr_est = fields.Char(
        string="State Tax Number",
        size=17,
        unaccent=False,
    )

    rg = fields.Char(
        string="RG",
        unaccent=False,
    )

    state_tax_number_ids = fields.One2many(
        string="Others State Tax Number",
        comodel_name="state.tax.numbers",
        inverse_name="partner_id",
    )

    inscr_mun = fields.Char(
        string="Municipal Tax Number",
        size=18,
        unaccent=False,
    )

    suframa = fields.Char(
        size=18,
        unaccent=False,
    )

    legal_name = fields.Char(
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
        size=32,
    )

    @api.depends("cnpj_cpf")
    def _compute_cnpj_cpf_stripped(self):
        for record in self:
            if record.cnpj_cpf:
                record.cnpj_cpf_stripped = "".join(
                    char for char in record.cnpj_cpf if char.isalnum()
                )
            else:
                record.cnpj_cpf_stripped = False

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        if self.is_br_partner:
            if default is None:
                default = {}
            if "vat" not in default:
                # CNPJ should be unique:
                default["vat"] = None
        return super().copy(default)

    @api.onchange("cnpj_cpf")
    def _inverse_cnpj_cpf(self):
        for partner in self:
            if partner.cnpj_cpf and len(re.sub("[^0-9]", "", partner.cnpj_cpf)) > 11:
                partner.vat = partner.cnpj_cpf
            else:
                partner.l10n_br_cpf_code = partner.cnpj_cpf

    @api.depends("vat", "l10n_br_cpf_code")
    def _compute_cnpj_cpf(self):
        for partner in self:
            partner.cnpj_cpf = partner.vat or partner.l10n_br_cpf_code

    @api.onchange("vat")
    def _onchange_vat(self):
        self.vat = cnpj_cpf.formata(str(self.vat))

    @api.onchange("zip")
    def _onchange_zip(self):
        self.zip = misc.format_zipcode(self.zip, self.country_id.code)

    # TODO: O metodo tanto no res.partner quanto no res.company chamam
    #  _onchange_state e aqui também deveria, porém por algum motivo
    #  ainda desconhecido se o metodo estiver com o mesmo nome não é
    #  chamado, por isso aqui está sendo adicionado o final _id
    @api.onchange("state_id")
    def _onchange_state_id(self):
        self.city_id = None

    @api.onchange("city_id")
    def _onchange_city_id(self):
        self.city = self.city_id.name
