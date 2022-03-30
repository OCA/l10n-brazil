# Copyright (C) 2012 - TODAY  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base import misc
    from erpbrasil.base.fiscal import cnpj_cpf, ie
except ImportError:
    _logger.error("erpbrasil.base library not installed")


class Lead(models.Model):
    """CRM Lead Case"""

    _name = "crm.lead"
    _inherit = [_name, "l10n_br_base.party.mixin", "format.address.mixin"]

    cnpj = fields.Char(string="CNPJ")

    street_name = fields.Char(string="Street Name")

    street_number = fields.Char(string="Street Number")

    name_surname = fields.Char(
        string="Name and Surname", help="Name used in fiscal documents"
    )

    cpf = fields.Char(string="CPF")

    @api.onchange("contact_name")
    def _onchange_contact_name(self):
        if not self.name_surname:
            self.name_surname = self.contact_name

    @api.constrains("cnpj")
    def _check_cnpj(self):
        for record in self:
            country_code = record.country_id.code or ""
            if record.cnpj and country_code.upper() == "BR":
                cnpj = misc.punctuation_rm(record.cnpj)
                if not cnpj_cpf.validar(cnpj):
                    raise ValidationError(_("Invalid CNPJ!"))
            return True

    @api.constrains("cpf")
    def _check_cpf(self):
        for record in self:
            country_code = record.country_id.code or ""
            if record.cpf and country_code.upper() == "BR":
                cpf = misc.punctuation_rm(record.cpf)
                if not cnpj_cpf.validar(cpf):
                    raise ValidationError(_("Invalid CPF!"))
            return True

    @api.constrains("inscr_est")
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False.
        """
        for record in self:
            result = True
            if record.inscr_est and record.cnpj and record.state_id:
                state_code = record.state_id.code or ""
                uf = state_code.lower()
                result = ie.validar(uf, record.inscr_est)
            if not result:
                raise ValidationError(_("Invalid State Tax Number!"))

    @api.onchange("cnpj", "country_id")
    def _onchange_cnpj(self):
        self.cnpj = cnpj_cpf.formata(self.cnpj)

    @api.onchange("cpf", "country_id")
    def _onchange_mask_cpf(self):
        self.cpf = cnpj_cpf.formata(self.cpf)

    @api.onchange("city_id")
    def _onchange_city_id(self):
        """Ao alterar o campo l10n_br_city_id que é um campo relacional
        com o l10n_br_base.city que são os municípios do IBGE, copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.
        param int l10n_br_city_id: id do l10n_br_city_id digitado.
        return: dicionário com o nome e id do município.
        """
        if self.city_id:
            self.city = self.city_id.name
        elif self.partner_id.city_id:
            self.city_id = self.partner_id.city_id
            self.city = self.partner_id.city_id.name

    @api.onchange("zip")
    def _onchange_zip(self):
        self.zip = misc.format_zipcode(self.zip, self.country_id.code)

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        result = super(Lead, self)._prepare_values_from_partner(self.partner_id)

        if self.partner_id:
            result["street_name"] = self.partner_id.street_name
            result["street_number"] = self.partner_id.street_number
            result["street2"] = self.partner_id.street2
            result["district"] = self.partner_id.district
            result["city_id"] = self.partner_id.city_id.id
            result["country_id"] = self.partner_id.country_id.id
            if self.partner_id.is_company:
                result["legal_name"] = self.partner_id.legal_name
                result["cnpj"] = self.partner_id.cnpj_cpf
                result["inscr_est"] = self.partner_id.inscr_est
                result["inscr_mun"] = self.partner_id.inscr_mun
                result["suframa"] = self.partner_id.suframa
            else:
                result["partner_name"] = self.partner_id.parent_id.name or False
                result["legal_name"] = self.partner_id.parent_id.legal_name or False
                result["cnpj"] = self.partner_id.parent_id.cnpj_cpf or False
                result["inscr_est"] = self.partner_id.parent_id.inscr_est or False
                result["inscr_mun"] = self.partner_id.parent_id.inscr_mun or False
                result["suframa"] = self.partner_id.parent_id.suframa or False
                result["website"] = self.partner_id.parent_id.website or False
                result["cpf"] = self.partner_id.cnpj_cpf
                result["rg"] = self.partner_id.rg
                result["name_surname"] = self.partner_id.legal_name
        self.update(result)

    def _prepare_customer_values(self, name, is_company, parent_id=False):
        """Extract data from lead to create a partner.
        :param name : furtur name of the partner
        :param is_company : True if the partner is a company
        :param parent_id : id of the parent partner (False if no parent)
        :return: dictionary of values to give at res_partner.create()
        """
        values = super()._prepare_customer_values(name, is_company, parent_id)
        values.update(
            {
                "legal_name": self.legal_name if is_company else self.name_surname,
                "street_name": self.street_name,
                "street_number": self.street_number,
                "district": self.district,
                "city_id": self.city_id.id,
            }
        )
        if is_company:
            values.update(
                {
                    "cnpj_cpf": self.cnpj,
                    "inscr_est": self.inscr_est,
                    "inscr_mun": self.inscr_mun,
                    "suframa": self.suframa,
                }
            )
        else:
            values.update(
                {
                    "cnpj_cpf": self.cpf,
                    "inscr_est": self.rg,
                    "rg": self.rg,
                }
            )
        return values
