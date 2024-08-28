# Copyright (C) 2024-Today - Engenere (<https://engenere.one>).
# @author Cristiano Mafra Junior
import logging

import requests
from erpbrasil.base import misc
from erpbrasil.base.fiscal import cnpj_cpf
from erpbrasil.base.misc import punctuation_rm

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PartnerCnpjSearchWizard(models.TransientModel):
    _name = "partner.search.wizard"
    _description = "CNPJ based search wizard allowing to update partner data."

    partner_id = fields.Many2one(comodel_name="res.partner")
    provider_name = fields.Char()
    cnpj_cpf = fields.Char()
    legal_name = fields.Char()
    name = fields.Char()
    inscr_est = fields.Char()
    zip = fields.Char()
    street_name = fields.Char()
    street_number = fields.Char()
    street2 = fields.Char()
    district = fields.Char()
    state_id = fields.Many2one(comodel_name="res.country.state")
    city_id = fields.Many2one(
        comodel_name="res.city",
        domain="[('state_id', '=', state_id)]",
    )
    country_id = fields.Many2one(comodel_name="res.country")
    phone = fields.Char()
    mobile = fields.Char()
    email = fields.Char()
    legal_nature = fields.Char()
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.ref("base.BRL"),
    )
    equity_capital = fields.Monetary(currency_field="currency_id")
    cnae_main_id = fields.Many2one(comodel_name="l10n_br_fiscal.cnae")
    cnae_secondary_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.cnae",
        relation="wizard_fiscal_cnae_rel",
        column1="company_id",
        column2="cnae_id",
    )
    child_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="parent_id_wizard_id",
        column1="parent_id",
        column2="wizard_id",
    )

    @api.onchange("zip")
    def _onchange_zip(self):
        self.zip = misc.format_zipcode(self.zip)

    @api.onchange("cnpj_cpf")
    def _onchange_cnpj_cpf(self):
        self.cnpj_cpf = cnpj_cpf.formata(str(self.cnpj_cpf))

    def _get_partner_values(self, cnpj_cpf):
        webservice = self.env["l10n_br_cnpj_search.webservice.abstract"]
        provider_name = webservice.get_provider()
        try:
            response = requests.get(
                webservice.get_api_url(cnpj_cpf),
                headers=webservice.get_headers(),
                timeout=5,
            )
        except requests.exceptions.Timeout:
            _logger.debug("Request timed out!")
        data = webservice.validate(response)
        values = webservice.import_data(data)
        values["provider_name"] = provider_name
        values["cnpj_cpf"] = cnpj_cpf
        return values

    def default_get(self, fields):
        res = super().default_get(fields)
        partner_id = self.env.context.get("default_partner_id")
        partner_model = self.env["res.partner"]
        partner = partner_model.browse(partner_id)
        cnpj_cpf = punctuation_rm(partner.cnpj_cpf)
        misc.punctuation_rm(self.zip)
        values = self._get_partner_values(cnpj_cpf)
        res.update(values)
        return res

    def action_update_partner(self):
        values_to_update = {
            "legal_name": self.legal_name,
            "name": self.name,
            "inscr_est": self.inscr_est,
            "zip": self.zip,
            "street_name": self.street_name,
            "street_number": self.street_number,
            "street2": self.street2,
            "district": self.district,
            "state_id": self.state_id.id,
            "city_id": self.city_id.id,
            "city": self.city_id.name,
            "country_id": self.country_id.id,
            "phone": self.phone,
            "mobile": self.mobile,
            "email": self.email,
            "legal_nature": self.legal_nature,
            "equity_capital": self.equity_capital,
            "cnae_main_id": self.cnae_main_id,
            "cnae_secondary_ids": self.cnae_secondary_ids,
            "company_type": "company",
        }
        if self.child_ids:
            values_to_update["child_ids"] = [(6, 0, self.child_ids.ids)]

        non_empty_values = {
            key: value for key, value in values_to_update.items() if value
        }
        if non_empty_values:
            # Update partner only if there are non-empty values
            self.partner_id.write(non_empty_values)
        return {"type": "ir.actions.act_window_close"}
