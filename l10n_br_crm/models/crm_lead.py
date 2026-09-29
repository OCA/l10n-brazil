# Copyright (C) 2012 - TODAY  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base.fiscal import cnpj_cpf

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import clean_context, parse_contact_from_email

from odoo.addons.l10n_br_base.tools import check_cnpj_cpf, check_ie


class Lead(models.Model):
    """CRM Lead Case"""

    _name = "crm.lead"
    _inherit = [_name, "l10n_br_base.party.mixin"]

    l10n_br_rg_code = fields.Char(string="RG")

    street_name = fields.Char()

    street_number = fields.Char()

    name_surname = fields.Char(
        string="Name and Surname", help="Name used in fiscal documents"
    )

    @api.depends("country_id", "partner_id.country_id")
    def _compute_show_l10n_br(self):
        """Show the Brazilian fields when the Lead or its Customer is Brazilian."""
        br_country = self.env.ref("base.br")
        for record in self:
            record.show_l10n_br = bool(
                record.country_id == br_country
                or record.partner_id.country_id == br_country
            )

    @api.onchange("contact_name")
    def _onchange_contact_name(self):
        if not self.name_surname:
            self.name_surname = self.contact_name

    @api.constrains("vat", "country_id")
    def _check_vat(self):
        for record in self:
            check_cnpj_cpf(record.env, record.vat, record.country_id)

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

    @api.onchange("city_id")
    def _onchange_city_id(self):
        """Ao alterar o campo l10n_br_city_id que é um campo relacional
        com o l10n_br_base.city que são os municípios do IBGE, copia o
        nome do município para o campo city que é o campo nativo do módulo base
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

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """Fill the Lead with the Customer data, Brazilian fiscal data included.

        Odoo 20.0 computes the core Lead fields from ``partner_id`` (see
        ``_compute_partner_address_values``), the Brazilian ones still need
        this sync. A contact of a company takes the fiscal data of its
        company, as the Brazilian documents are issued to the company.
        """
        result = super()._prepare_values_from_partner(self.partner_id)

        if self.partner_id:
            partner = self.partner_id
            parent = partner.parent_id
            result.update(
                {
                    "street_name": partner.street_name,
                    "street_number": partner.street_number,
                    "street2": partner.street2,
                    "district": partner.district,
                    "city_id": partner.city_id.id,
                    "country_id": partner.country_id.id,
                    "vat": partner.vat
                    if partner.is_company
                    else parent.vat or partner.vat,
                }
            )
            result = self._convert_to_write(result)
            if partner.country_id.code == "BR":
                self._normalize_vat(result)
            if partner.is_company:
                result["legal_name"] = partner.legal_name
                result["l10n_br_ie_code"] = partner.l10n_br_ie_code
                result["l10n_br_im_code"] = partner.l10n_br_im_code
                result["l10n_br_isuf_code"] = partner.l10n_br_isuf_code
            else:
                result["partner_name"] = parent.name or False
                result["legal_name"] = parent.legal_name or False
                result["l10n_br_ie_code"] = parent.l10n_br_ie_code or False
                result["l10n_br_im_code"] = parent.l10n_br_im_code or False
                result["l10n_br_isuf_code"] = parent.l10n_br_isuf_code or False
                result["website"] = parent.website or False
                result["l10n_br_rg_code"] = partner.l10n_br_rg_code
                result["name_surname"] = partner.legal_name
        self.update(result)
        return result

    def _is_br_company(self):
        """Whether the Lead holds a CNPJ, i.e. is a company in Brazil."""
        return bool(self.vat and cnpj_cpf.validar_cnpj(self.vat))

    def _create_customer(self):
        """Create a partner from the Lead data and link it to the Lead.

        Same as the core method, except that in Brazil the customer company is
        created before the contact person: Odoo 20.0 creates the contact first
        and lets it create its company from ``parent_name``, both carrying the
        ``vat`` of the Lead, which cannot be done here as the CNPJ identifies
        the company and two partners cannot share it (see l10n_br_base).
        """
        self.ensure_one()
        Partner = self.env["res.partner"].with_context(clean_context(self.env.context))
        contact_name = self.contact_name
        if not contact_name:
            contact_name = (
                parse_contact_from_email(self.email_from)[0]
                if self.email_from
                else False
            )

        partner_company = self.partner_id
        if not partner_company and self.partner_name and self._is_br_company():
            partner_company = Partner.create(
                self._prepare_customer_values(self.partner_name)
            )

        if contact_name:
            return Partner.create(
                self._prepare_customer_values(
                    contact_name, parent_id=partner_company.id
                )
            )
        if partner_company:
            return partner_company
        return Partner.create(self._prepare_customer_values(self.name))

    def _prepare_customer_values(self, partner_name, parent_id=False):
        """Extract data from lead to create a partner.

        :param partner_name : future name of the partner
        :param parent_id : id of the parent partner (False if no parent)
        :return: dictionary of values to give at res_partner.create()
        """
        values = super()._prepare_customer_values(partner_name, parent_id=parent_id)
        # A Brazilian company is created from its own CNPJ and company name,
        # never from the free text ``partner_name`` of the Lead: another
        # partner would hold the same CNPJ, which l10n_br_base forbids.
        values.pop("parent_name", None)
        # Odoo 20.0 removed the Person/Company switch, the company case is
        # deduced from the CNPJ and the individual case from the CPF (same
        # rule as res.partner._compute_is_company in l10n_br_base). A partner
        # created under another one is a contact, not the company itself.
        is_company = self._is_br_company() and not parent_id
        vat = self.vat
        if parent_id and self._is_br_company():
            # the CNPJ belongs to the company (the parent partner)
            vat = False
        values.update(
            {
                "legal_name": self.legal_name if is_company else self.name_surname,
                "street_name": self.street_name,
                "street_number": self.street_number,
                "district": self.district,
                "city_id": self.city_id.id,
                "vat": vat,
            }
        )
        if self.vat and not values.get("country_id"):
            values["country_id"] = self.env.ref("base.br").id
        self._normalize_vat(values)
        if is_company:
            values.update(
                {
                    "l10n_br_ie_code": self.l10n_br_ie_code,
                    "l10n_br_im_code": self.l10n_br_im_code,
                    "l10n_br_isuf_code": self.l10n_br_isuf_code,
                }
            )
        else:
            values.update(
                {
                    "l10n_br_ie_code": self.l10n_br_rg_code,
                    "l10n_br_rg_code": self.l10n_br_rg_code,
                }
            )
        return values

    def action_open_cnpj_search_wizard(self):
        if not self.vat:
            raise UserError(self.env._("Please enter your CNPJ"))
        if self.cnpj_validation_disabled():
            raise UserError(
                self.env._(
                    "It is necessary to activate the option to validate de CNPJ to use"
                    " this functionality."
                )
            )
        context = {
            "active_model": self._name,
        }
        if self._name == "res.partner":
            context["default_partner_id"] = self.id
        elif self._name == "crm.lead":
            context["default_lead_id"] = self.id
        else:
            context["default_partner_id"] = self.partner_id.id

        return {
            "name": "Search Data by CNPJ",
            "type": "ir.actions.act_window",
            "res_model": "partner.search.wizard",
            "view_type": "form",
            "view_mode": "form",
            "context": context,
            "target": "new",
        }

    @api.model
    def cnpj_validation_disabled(self):
        """Whether the CPF/CNPJ validation is disabled.

        Kept for the users of this method (l10n_br_cnpj_search wizards), the
        setting itself is handled by the l10n_br_base mixin.
        """
        return self._l10n_br_disable_vat_validation()
