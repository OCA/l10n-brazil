# Copyright (C) 2024-Today - Engenere (<https://engenere.one>).
# @author Cristiano Mafra Junior
import logging
from unittest.mock import patch

import requests
from erpbrasil.base import misc
from erpbrasil.base.fiscal import cnpj_cpf
from erpbrasil.base.misc import punctuation_rm

from odoo import Command, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import TAX_FRAMEWORK

from ..models.l10n_br_base_party_mixin import CNPJ_BRANCH_TYPE_SELECTION

_logger = logging.getLogger(__name__)
# This is the original 'send' method from the requests library that
# Odoo's test suite patches over.
_original_send = requests.Session.send


class PartnerCnpjSearchWizard(models.TransientModel):
    _name = "partner.search.wizard"
    _description = "CNPJ based search wizard allowing to update partner data."

    partner_id = fields.Many2one(comodel_name="res.partner")
    provider_name = fields.Char()
    vat = fields.Char(string="CNPJ")
    legal_name = fields.Char()
    name = fields.Char()
    l10n_br_ie_code = fields.Char()
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
    legal_nature_id = fields.Many2one(comodel_name="l10n_br_fiscal.legal.nature")
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.ref("base.BRL"),
    )
    equity_capital = fields.Monetary(currency_field="currency_id")
    cnae_main_id = fields.Many2one(comodel_name="l10n_br_fiscal.cnae")
    tax_framework = fields.Selection(selection=TAX_FRAMEWORK)
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
    company_size = fields.Char()
    cnpj_status = fields.Char()
    cnpj_status_date = fields.Date()
    cnpj_status_reason = fields.Char()
    opening_date = fields.Date()
    cnpj_branch_type = fields.Selection(selection=CNPJ_BRANCH_TYPE_SELECTION)
    simples_option_date = fields.Date()
    legal_responsible_name = fields.Char()
    legal_responsible_function = fields.Char()
    cnpj_card_pdf = fields.Binary(attachment=False)

    @api.onchange("zip")
    def _onchange_zip(self):
        self.zip = misc.format_zipcode(self.zip)

    @api.onchange("vat")
    def _onchange_vat(self):
        if self.vat:
            self.vat = cnpj_cpf.formata(str(self.vat))

    def _get_partner_values(self, vat):
        webservice = self.env["l10n_br_cnpj_search.webservice.abstract"]
        provider_name = webservice.get_provider()
        with patch("requests.Session.send", _original_send):
            try:
                response = requests.get(
                    webservice.get_api_url(vat),
                    headers=webservice.get_headers(),
                    timeout=5,
                )
            except requests.exceptions.Timeout as exc:
                _logger.warning(
                    "CNPJ search request timed out (provider: %s)",
                    provider_name,
                    exc_info=True,
                )
                raise UserError(
                    self.env._("The CNPJ search service did not respond in time.")
                ) from exc
        data = webservice.validate(response)
        values = webservice.import_data(data)
        values["provider_name"] = provider_name
        values["vat"] = vat

        if provider_name == "cpfcnpj" and webservice._cpfcnpj_get_bool_param(
            "cpfcnpj_fetch_ie", default=False
        ):
            ie_code = self._fetch_cpfcnpj_ie(webservice, vat, data)
            if ie_code:
                values["l10n_br_ie_code"] = ie_code

        return values

    def _fetch_cpfcnpj_ie(self, webservice, vat, main_data):
        """Fetch the state registration (package 16) with a second request.

        This is best effort: any failure is logged and swallowed so it never
        breaks the main lookup. The active registration matching the
        establishment UF is preferred.
        """
        try:
            url = webservice.cpfcnpj_get_api_url(vat, package="16")
            with patch("requests.Session.send", _original_send):
                response = requests.get(
                    url,
                    headers=webservice.get_headers(),
                    timeout=5,
                )
            if response.status_code != 200:
                return False
            ie_data = response.json()
            uf = (main_data.get("matrizEndereco") or {}).get("uf")
            return webservice._cpfcnpj_select_ie(ie_data, uf)
        except (requests.RequestException, ValueError):
            _logger.warning("CPF.CNPJ state registration lookup failed", exc_info=True)
            return False

    def default_get(self, fields):
        res = super().default_get(fields)
        partner_id = self.env.context.get("default_partner_id")
        if partner_id:
            partner = self.env["res.partner"].browse(partner_id)
            vat = punctuation_rm(partner.vat)
            values = self._get_partner_values(vat)
            res.update(values)
        return res

    def action_update_partner(self):
        values_to_update = {
            "legal_name": self.legal_name,
            "name": self.name,
            "l10n_br_ie_code": self.l10n_br_ie_code,
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
            "legal_nature_id": self.legal_nature_id,
            "equity_capital": self.equity_capital,
            "cnae_main_id": self.cnae_main_id,
            "cnae_secondary_ids": self.cnae_secondary_ids,
            "tax_framework": self.tax_framework,
            "company_size": self.company_size,
            "cnpj_status": self.cnpj_status,
            "cnpj_status_date": self.cnpj_status_date,
            "cnpj_status_reason": self.cnpj_status_reason,
            "opening_date": self.opening_date,
            "cnpj_branch_type": self.cnpj_branch_type,
            "simples_option_date": self.simples_option_date,
            "legal_responsible_name": self.legal_responsible_name,
            "legal_responsible_function": self.legal_responsible_function,
            "company_type": "company",
        }
        if self.vat:
            values_to_update["vat"] = punctuation_rm(self.vat)
        if self.child_ids:
            values_to_update["child_ids"] = [Command.set(self.child_ids.ids)]

        non_empty_values = {
            key: value for key, value in values_to_update.items() if value
        }
        if non_empty_values:
            # Update partner only if there are non-empty values
            self.partner_id.write(non_empty_values)

        if self.cnpj_card_pdf:
            self._attach_cnpj_card()
        return {"type": "ir.actions.act_window_close"}

    def _attach_cnpj_card(self):
        """Store the CNPJ card PDF as an attachment on the partner.

        A previous card with the same name is replaced in place instead of
        being duplicated.
        """
        self.ensure_one()
        partner = self.partner_id
        cnpj_digits = punctuation_rm(self.vat) if self.vat else ""
        name = f"Cartao_CNPJ_{cnpj_digits}.pdf"
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "res.partner"),
                ("res_id", "=", partner.id),
                ("name", "=", name),
            ],
            limit=1,
        )
        if attachment:
            attachment.write({"datas": self.cnpj_card_pdf})
        else:
            self.env["ir.attachment"].create(
                {
                    "name": name,
                    "res_model": "res.partner",
                    "res_id": partner.id,
                    "mimetype": "application/pdf",
                    "datas": self.cnpj_card_pdf,
                    "type": "binary",
                }
            )
