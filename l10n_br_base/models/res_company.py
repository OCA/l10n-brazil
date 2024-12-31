# 2013 Copyright (C) Thinkopen Solutions (<http://www.thinkopensolutions.com.br>)
# 2013 Copyright (C) Akretion (<http://www.akretion.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.exceptions import UserError


class Company(models.Model):
    _name = "res.company"
    _inherit = [_name, "format.address.mixin", "l10n_br_base.party.mixin"]

    def _get_company_address_field_names(self):
        partner_fields = super()._get_company_address_field_names()
        return partner_fields + [
            "legal_name",
            "cnpj_cpf",
            "l10n_br_ie_code",
            "l10n_br_im_code",
            "district",
            "city_id",
            "l10n_br_isuf_code",
            "state_tax_number_ids",
            "street_number",
            "street_name",
        ]

    def _inverse_legal_name(self):
        for company in self:
            company.partner_id.legal_name = company.legal_name

    def _inverse_district(self):
        for company in self:
            company.partner_id.district = company.district

    def _inverse_street_name(self):
        for company in self:
            company.partner_id.street_name = company.street_name

    def _inverse_street_number(self):
        for company in self:
            company.partner_id.street_number = company.street_number

    def _inverse_cnpj_cpf(self):
        for company in self:
            company.partner_id.cnpj_cpf = company.cnpj_cpf

    def _inverse_l10n_br_ie_code(self):
        for company in self:
            company.partner_id.l10n_br_ie_code = company.l10n_br_ie_code

    def _inverse_state(self):
        for company in self:
            company.partner_id.state_id = company.state_id

    def _inverse_state_tax_number_ids(self):
        """Write the l10n_br specific functional fields."""
        for company in self:
            state_tax_number_ids = self.env["state.tax.numbers"]
            for ies in company.state_tax_number_ids:
                state_tax_number_ids |= ies
            company.partner_id.state_tax_number_ids = state_tax_number_ids

    def _inverse_l10n_br_im_code(self):
        """Write the l10n_br specific functional fields."""
        for company in self:
            company.partner_id.l10n_br_im_code = company.l10n_br_im_code

    def _inverse_city_id(self):
        """Write the l10n_br specific functional fields."""
        for company in self:
            company.partner_id.city_id = company.city_id

    def _inverse_l10n_br_isuf_code(self):
        """Write the l10n_br specific functional fields."""
        for company in self:
            company.partner_id.l10n_br_isuf_code = company.l10n_br_isuf_code

    legal_name = fields.Char(
        compute="_compute_address",
        inverse="_inverse_legal_name",
    )

    district = fields.Char(
        compute="_compute_address",
        inverse="_inverse_district",
    )

    street_name = fields.Char(
        compute="_compute_address",
        inverse="_inverse_street_name",
    )

    street_number = fields.Char(
        compute="_compute_address",
        inverse="_inverse_street_number",
    )

    city_id = fields.Many2one(
        domain="[('state_id', '=', state_id)]",
        compute="_compute_address",
        inverse="_inverse_city_id",
    )

    country_id = fields.Many2one(default=lambda self: self.env.ref("base.br"))

    cnpj_cpf = fields.Char(
        compute="_compute_address",
        inverse="_inverse_cnpj_cpf",
    )

    l10n_br_ie_code = fields.Char(
        compute="_compute_address",
        inverse="_inverse_l10n_br_ie_code",
    )

    state_tax_number_ids = fields.One2many(
        string="State Tax Numbers",
        comodel_name="state.tax.numbers",
        inverse_name="company_id",
        compute="_compute_address",
        inverse="_inverse_state_tax_number_ids",
    )

    l10n_br_im_code = fields.Char(
        compute="_compute_address",
        inverse="_inverse_l10n_br_im_code",
    )

    l10n_br_isuf_code = fields.Char(
        compute="_compute_address",
        inverse="_inverse_l10n_br_isuf_code",
    )

    @api.model
    def _fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        res = super()._fields_view_get(view_id, view_type, toolbar, submenu)
        if view_type == "form":
            res["arch"] = self._view_get_address(res["arch"])
        return res

    def write(self, values):
        """
        Overriden so we can change the currency_id of base.main_company
        in l10n_br_base/demo/res_company_demo.xml (demo data)
        """
        try:
            result = super().write(values)
        except UserError as e:
            demo_main_company = self.env.ref(
                "base.main_company", raise_if_not_found=False
            )
            brl_currency = self.env.ref("base.BRL")
            if (
                demo_main_company
                and self.ids == [demo_main_company.id]
                and values.get("currency_id") == brl_currency.id
            ):
                result = models.Model.write(self, values)
            else:
                raise e

        return result

    @api.onchange("state_id")
    def _onchange_state_id(self):
        res = super()._onchange_state_id()
        self.l10n_br_ie_code = False
        self.partner_id.l10n_br_ie_code = False
        self.partner_id.state_id = self.state_id
        return res
