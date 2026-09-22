# 2013 Copyright (C) Thinkopen Solutions (<http://www.thinkopensolutions.com.br>)
# 2013 Copyright (C) Akretion (<http://www.akretion.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class Company(models.Model):
    _name = "res.company"
    _inherit = [_name, "format.address.mixin", "l10n_br_base.party.mixin"]

    def _get_company_address_field_names(self):
        partner_fields = super()._get_company_address_field_names()
        return partner_fields + [
            "legal_name",
            "l10n_br_ie_code",
            "l10n_br_im_code",
            "district",
            "city_id",
            "l10n_br_isuf_code",
            "state_tax_number_ids",
            "street_number",
            "street_name",
            "street_number2",
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

    def _inverse_street_number2(self):
        for company in self:
            company.partner_id.street_number2 = company.street_number2

    def _inverse_l10n_br_ie_code(self):
        for company in self:
            company.partner_id.l10n_br_ie_code = company.l10n_br_ie_code

    def _get_non_stored_address_field_names(self):
        """Company address fields that stay computed without storage."""
        return ["l10n_br_im_code", "l10n_br_isuf_code", "state_tax_number_ids"]

    @api.depends(
        lambda self: [
            f"partner_id.{fname}" for fname in self._get_company_address_field_names()
        ]
    )
    def _compute_address(self):
        """Read the company address (and its Brazilian attributes) on the
        company partner.

        Differences with the core implementation: the address fields are stored
        again (their compute/inverse methods used to be a placeholder of the
        core ``_compute_address`` back when ``res.company`` inherited
        ``res.partner``) and ``company.update()`` cannot be used anymore since
        it assigns the raw values of the partner - records for the many2one
        fields - which cannot be flushed to a stored column. Assigning the
        fields one by one lets the ORM convert the values.

        Only the stored fields are computed here: Odoo warns when a compute
        method serves both stored and non stored fields (see
        ``_compute_l10n_br_partner_fields`` for the latter).
        """
        for company in self.filtered(lambda company: company.partner_id):
            address_data = company.partner_id.sudo().address_get(adr_pref=["contact"])
            if address_data["contact"]:
                partner = company.partner_id.browse(address_data["contact"]).sudo()
                for fname in company._get_company_address_field_names():
                    if company._fields[fname].store:
                        company[fname] = partner[fname]

    @api.depends(
        lambda self: [
            f"partner_id.{fname}"
            for fname in self._get_non_stored_address_field_names()
        ]
    )
    def _compute_l10n_br_partner_fields(self):
        """Read the non stored Brazilian fields on the company partner."""
        for company in self.filtered(lambda company: company.partner_id):
            partner = company.partner_id
            for fname in company._get_non_stored_address_field_names():
                company[fname] = partner[fname]

    def _prepare_address_values(self, vals):
        """Accept records as well as ids for the address fields.

        The core instance passes ids, but the fields were not stored before, so
        existing call sites (test fixtures among others) pass records.
        """
        for fname in self._get_company_address_field_names():
            if isinstance(vals.get(fname), models.BaseModel):
                vals[fname] = vals[fname].id
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._prepare_address_values(vals)
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        self._prepare_address_values(vals)
        return super().write(vals)

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

    # Odoo 19 turned the address fields of res.company into computed fields
    # without storage: assigning them is a no-op and reading them recomputes
    # (via the core address compute, which writes on the company). Store them
    # again so the company address keeps working for the whole code base, both
    # for reading and writing; the company partner stays the source of truth
    # (the compute reads it and the inverse methods write on it).
    legal_name = fields.Char(
        compute="_compute_address",
        inverse="_inverse_legal_name",
        store=True,
    )

    district = fields.Char(
        compute="_compute_address",
        inverse="_inverse_district",
        store=True,
    )

    street_name = fields.Char(
        compute="_compute_address",
        inverse="_inverse_street_name",
        store=True,
    )

    street_number = fields.Char(
        compute="_compute_address",
        inverse="_inverse_street_number",
        store=True,
    )

    street_number2 = fields.Char(
        compute="_compute_address",
        inverse="_inverse_street_number2",
        store=True,
    )

    city_id = fields.Many2one(
        domain="[('state_id', '=', state_id)]",
        compute="_compute_address",
        inverse="_inverse_city_id",
        store=True,
    )

    country_id = fields.Many2one(
        "res.country",
        compute="_compute_address",
        inverse="_inverse_country",
        store=True,
        default=lambda self: self.env.ref("base.br"),
    )

    state_id = fields.Many2one(
        "res.country.state",
        compute="_compute_address",
        inverse="_inverse_state",
        store=True,
    )

    street = fields.Char(
        compute="_compute_address", inverse="_inverse_street", store=True
    )

    street2 = fields.Char(
        compute="_compute_address", inverse="_inverse_street2", store=True
    )

    zip = fields.Char(compute="_compute_address", inverse="_inverse_zip", store=True)

    city = fields.Char(compute="_compute_address", inverse="_inverse_city", store=True)

    l10n_br_ie_code = fields.Char(
        compute="_compute_address",
        inverse="_inverse_l10n_br_ie_code",
        store=True,
    )

    state_tax_number_ids = fields.One2many(
        string="State Tax Numbers",
        comodel_name="state.tax.numbers",
        inverse_name="company_id",
        compute="_compute_l10n_br_partner_fields",
        inverse="_inverse_state_tax_number_ids",
    )

    l10n_br_im_code = fields.Char(
        compute="_compute_l10n_br_partner_fields",
        inverse="_inverse_l10n_br_im_code",
    )

    l10n_br_isuf_code = fields.Char(
        compute="_compute_l10n_br_partner_fields",
        inverse="_inverse_l10n_br_isuf_code",
    )

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "form":
            arch = self._view_get_address(arch)
        return arch, view

    @api.onchange("state_id")
    def _onchange_state_id(self):
        res = super()._onchange_state_id()
        self.l10n_br_ie_code = False
        self.partner_id.l10n_br_ie_code = False
        self.partner_id.state_id = self.state_id
        return res
