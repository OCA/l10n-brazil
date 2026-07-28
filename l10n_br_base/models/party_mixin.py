# Copyright (C) 2021 Renato Lima (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base import misc
from erpbrasil.base.fiscal import cnpj_cpf

from odoo import api, fields, models


class PartyMixin(models.AbstractModel):
    _name = "l10n_br_base.party.mixin"
    _description = "Brazilian partner and company data mixin"

    vat = fields.Char()  # mixin methods needs the vat field here

    cnpj_cpf_stripped = fields.Char(
        string="CNPJ/CPF Stripped",
        help="CNPJ/CPF without special characters",
        compute="_compute_cnpj_cpf_stripped",
        store=True,
        # trigram GIN index to speed up the leading-wildcard ilike issued by
        # name_search (see _rec_names_search on res.partner). The value is
        # alphanumeric and never accented, so the index is always used.
        index="trigram",
    )

    vat_formatted_cnpj = fields.Char(
        string="VAT Formatted (Brazil)",
        compute="_compute_vat_formatted_cnpj",
        help="CNPJ or CPF formatted with proper punctuation and special characters",
    )

    show_br_vat_format = fields.Boolean(
        compute="_compute_show_br_vat_format",
        help="Whether to display VAT with Brazilian formatting (true when the"
        " current user's company is Brazilian).",
    )

    l10n_br_ie_code = fields.Char(
        string="State Tax Number",
        size=17,
        # trigram: alphanumeric value, index and query stay on the raw column
        # so the GIN index accelerates the ilike unconditionally.
        index="trigram",
    )

    state_tax_number_ids = fields.One2many(
        string="Others State Tax Number",
        comodel_name="state.tax.numbers",
        inverse_name="partner_id",
    )

    l10n_br_im_code = fields.Char(
        string="Municipal Tax Number",
        size=18,
    )

    l10n_br_isuf_code = fields.Char(
        string="Suframa",
        size=18,
    )

    legal_name = fields.Char(
        size=128,
        help="Used in fiscal documents",
        # trigram GIN index to speed up the name_search ilike on legal_name.
        # Names carry accents and must match accent-insensitively; the index
        # is only effective when the database `unaccent` function is
        # IMMUTABLE (INDEXABLE): only then does Odoo build the index on
        # unaccent(legal_name), matching the unaccent(col) like unaccent(%s)
        # query. On a stock PostgreSQL the contrib unaccent is STABLE, not
        # immutable, so the index is built on the raw column and the planner
        # cannot use it. See the PR body.
        index="trigram",
    )

    city_id = fields.Many2one(
        string="City of Address",
        comodel_name="res.city",
        domain="[('state_id', '=', state_id)]",
    )

    country_id = fields.Many2one(
        comodel_name="res.country",
        default=lambda self: self._default_country_id(),
    )

    district = fields.Char(
        size=32,
    )

    show_l10n_br = fields.Boolean(
        compute="_compute_show_l10n_br",
        help="Should display Brazilian localization fields?",
    )

    def _default_country_id(self):
        """Default country set to Brazil if the current company is Brazilian.
        Can be overridden in other modules if needed.
        """
        return (
            self.env.ref("base.br")
            if self.env.company.country_id.code == "BR"
            else False
        )

    @api.model
    def _expand_vat_search_domain(self, domain):
        """Expand simple ``vat ilike`` domain leaves so searching with a
        formatted CNPJ/CPF (with punctuation) also matches, even though
        ``vat`` is stored unformatted. The punctuation-stripped term is
        matched against the indexed ``cnpj_cpf_stripped`` field.
        """
        if self.env.context.get("no_stripped_match"):
            return domain
        new_domain = []
        for term in domain:
            if (
                isinstance(term, list | tuple)
                and len(term) == 3
                and term[0] == "vat"
                and term[1] in ("ilike", "=ilike")
                and term[2]
            ):
                stripped = "".join(char for char in str(term[2]) if char.isalnum())
                if stripped and stripped != term[2]:
                    new_domain += [
                        "|",
                        ("vat", term[1], term[2]),
                        ("cnpj_cpf_stripped", term[1], stripped),
                    ]
                    continue
            new_domain.append(term)
        return new_domain

    @api.model
    def _search(
        self,
        domain,
        offset=0,
        limit=None,
        order=None,
        *,
        active_test=True,
        bypass_access=False,
    ):
        return super()._search(
            self._expand_vat_search_domain(domain),
            offset=offset,
            limit=limit,
            order=order,
            active_test=active_test,
            bypass_access=bypass_access,
        )

    @api.depends("vat")
    def _compute_cnpj_cpf_stripped(self):
        for record in self:
            if record.vat:
                record.cnpj_cpf_stripped = "".join(
                    char for char in record.vat if char.isalnum()
                )
            else:
                record.cnpj_cpf_stripped = False

    @api.depends("vat", "country_id")
    def _compute_vat_formatted_cnpj(self):
        for record in self:
            vat_formatted_cnpj = False
            if record.vat and record.country_id and record.country_id.code == "BR":
                vat_formatted_cnpj = cnpj_cpf.formata(record.vat)
            record.vat_formatted_cnpj = vat_formatted_cnpj

    @api.depends_context("company")
    def _compute_show_br_vat_format(self):
        br_company = self.env.company.country_id.code == "BR"
        for record in self:
            record.show_br_vat_format = br_company

    @api.onchange("zip")
    def _onchange_zip(self):
        if self.country_id:
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

    @api.onchange("vat")
    def _onchange_vat(self):
        """Keep VAT unformatted; the formatted value is available via
        vat_formatted_cnpj.
        """
        if self.vat:
            vals = {"vat": self.vat}
            self._normalize_vat(vals)
            self.vat = vals["vat"]

    @api.model
    def _normalize_vat(self, vals):
        """Strip punctuation from Brazilian VAT values so they are stored
        unformatted.
        """
        if not isinstance(vals, dict):
            return
        vat = vals.get("vat")
        if not vat:
            return
        country_id = vals.get("country_id")
        if country_id:
            country = self.env["res.country"].browse(country_id)
        elif self and len(self) == 1:
            country = self.country_id
        else:
            country = self.env.company.country_id
        if country and country.code == "BR":
            vals["vat"] = misc.punctuation_rm(str(vat))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._normalize_vat(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._normalize_vat(vals)
        return super().write(vals)

    @api.depends("country_id")
    def _compute_show_l10n_br(self):
        """
        Defines when Brazilian localization fields should be displayed.
        """
        for record in self:
            show_l10n_br = False
            if record.country_id == record.env.ref("base.br"):
                show_l10n_br = True
            record.show_l10n_br = show_l10n_br
