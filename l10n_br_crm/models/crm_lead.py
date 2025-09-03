# Copyright (C) 2012 - TODAY  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base import misc
from erpbrasil.base.fiscal import cnpj_cpf

from odoo import api, fields, models

from odoo.addons.l10n_br_base.tools import check_cnpj_cpf, check_ie


class Lead(models.Model):
    """CRM Lead Case"""

    _name = "crm.lead"
    _inherit = [_name, "l10n_br_base.party.mixin"]

    cnpj = fields.Char(string="CNPJ", unaccent=False)

    cpf = fields.Char(string="CPF", unaccent=False)

    l10n_br_rg_code = fields.Char(string="RG", unaccent=False)

    street_name = fields.Char()

    street_number = fields.Char()

    name_surname = fields.Char(
        string="Name and Surname", help="Name used in fiscal documents"
    )

    show_l10n_br = fields.Boolean(
        compute="_compute_show_l10n_br",
        help="Indicates if Brazilian localization fields should be displayed.",
    )

    @api.depends("country_id")
    def _compute_show_l10n_br(self):
        """
        Defines when Brazilian localization fields should be displayed.
        """
        for record in self:
            show_l10n_br = False
            if record.partner_id and record.partner_id.country_id == self.env.ref(
                "base.br"
            ):
                show_l10n_br = True
            elif record.country_id == self.env.ref("base.br"):
                show_l10n_br = True

            record.show_l10n_br = show_l10n_br

            # Apesar do metodo create ter os campos informados
            # o metodo _prepare_address_values_from_partner esta sendo
            # chamado com o partner vazio e os campos abaixo com False
            # o que acaba apagando os campos, por enquanto essa é a forma
            # encontrada para contornar o problema.
            # TODO: revalidar nas migrações
            partner = record.partner_id
            if partner:
                result = {
                    "street_name": partner.street_name,
                    "street_number": partner.street_number,
                    "district": partner.district,
                    "city_id": partner.city_id.id,
                }
                record.update(result)

    @api.onchange("contact_name")
    def _onchange_contact_name(self):
        if not self.name_surname:
            self.name_surname = self.contact_name

    @api.constrains("cnpj")
    def _check_cnpj(self):
        for record in self:
            check_cnpj_cpf(record.env, record.cnpj, record.country_id)

    @api.constrains("cpf")
    def _check_cpf(self):
        for record in self:
            check_cnpj_cpf(record.env, record.cpf, record.country_id)

    @api.constrains("l10n_br_ie_code")
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False.
        """
        for record in self:
            check_ie(
                record.env, record.l10n_br_ie_code, record.state_id, record.country_id
            )

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
        result = super()._prepare_values_from_partner(self.partner_id)

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
                result["l10n_br_ie_code"] = self.partner_id.l10n_br_ie_code
                result["l10n_br_im_code"] = self.partner_id.l10n_br_im_code
                result["l10n_br_isuf_code"] = self.partner_id.l10n_br_isuf_code
            else:
                result["partner_name"] = self.partner_id.parent_id.name or False
                result["legal_name"] = self.partner_id.parent_id.legal_name or False
                result["cnpj"] = self.partner_id.parent_id.cnpj_cpf or False
                result["l10n_br_ie_code"] = (
                    self.partner_id.parent_id.l10n_br_ie_code or False
                )
                result["l10n_br_im_code"] = (
                    self.partner_id.parent_id.l10n_br_im_code or False
                )
                result["l10n_br_isuf_code"] = (
                    self.partner_id.parent_id.l10n_br_isuf_code or False
                )
                result["website"] = self.partner_id.parent_id.website or False
                result["cpf"] = self.partner_id.cnpj_cpf
                result["l10n_br_rg_code"] = self.partner_id.l10n_br_rg_code
                result["name_surname"] = self.partner_id.legal_name
        self.update(result)
        return result

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
                    "l10n_br_ie_code": self.l10n_br_ie_code,
                    "l10n_br_im_code": self.l10n_br_im_code,
                    "l10n_br_isuf_code": self.l10n_br_isuf_code,
                }
            )
        else:
            values.update(
                {
                    "cnpj_cpf": self.cpf,
                    "l10n_br_ie_code": self.l10n_br_rg_code,
                    "l10n_br_rg_code": self.l10n_br_rg_code,
                }
            )
        return values
