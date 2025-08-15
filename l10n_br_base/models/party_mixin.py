# Copyright (C) 2021 Renato Lima (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base import misc
from erpbrasil.base.fiscal import cnpj_cpf

from odoo import api, fields, models
from odoo.osv import expression


class PartyMixin(models.AbstractModel):
    _name = "l10n_br_base.party.mixin"
    _description = "Brazilian partner and company data mixin"

    vat = fields.Char()  # mixin methods needs the vat field here
    cnpj_cpf = fields.Char(  # alias for v14 backward compat
        string="CNPJ/CPF",
        # (for some reason related="vat" makes numerous tests fail)
        inverse="_inverse_cnpj_cpf",
        compute="_compute_cnpj_cpf",
        copy=False,
    )

    cnpj_cpf_stripped = fields.Char(
        string="CNPJ/CPF Stripped",
        help="CNPJ/CPF without special characters",
        compute="_compute_cnpj_cpf_stripped",
        store=True,
        index=True,
    )

    l10n_br_ie_code = fields.Char(
        string="State Tax Number",
        size=17,
        unaccent=False,
    )

    # compat with legacy code:
    inscr_est = fields.Char(
        related="l10n_br_ie_code", string="State Tax Number alias", readonly=False
    )

    state_tax_number_ids = fields.One2many(
        string="Others State Tax Number",
        comodel_name="state.tax.numbers",
        inverse_name="partner_id",
    )

    l10n_br_im_code = fields.Char(
        string="Municipal Tax Number",
        size=18,
        unaccent=False,
    )

    # backward compat with v14:
    inscr_mun = fields.Char(
        related="l10n_br_im_code", string="Municipal Tax Number alias", readonly=False
    )

    l10n_br_isuf_code = fields.Char(
        string="Suframa",
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
        comodel_name="res.country",
        default=lambda self: self._default_country_id(),
    )

    district = fields.Char(
        size=32,
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

    def _inverse_cnpj_cpf(self):
        for partner in self:
            partner.vat = cnpj_cpf.formata(str(self.cnpj_cpf))

    @api.model
    def search(self, domain, offset=0, limit=None, order=None, count=False):
        """in the case of a simple search with only OR terms and a vat ilike condition,
        inject the possibility to match the cnpj_cpf_stripped field.
        """
        if not any(term == "&" for term in domain) and not self._context.get(
            "no_stripped_match"
        ):
            for term in domain:
                if (
                    isinstance(term, list | tuple)
                    and len(term) == 3
                    and term[0] == "vat"
                    and term[1] == "ilike"
                ):
                    domain = expression.OR(
                        [domain, [("cnpj_cpf_stripped", "ilike", term[2])]]
                    )
                    break
        return super().search(domain, offset, limit, order, count)

    @api.onchange("cnpj_cpf")
    def _onchange_cnpj_cpf(self):  # TODO, see comment bellow
        """
        In the future we should simply put @api.onchange("cnpj_cpf")
        on _inverse_cnpj_cpf and remove this method. But for now,
        it's good to maintain backward compat with the v14 codebase with this.
        """
        return self._inverse_cnpj_cpf()

    @api.depends("vat")
    def _compute_cnpj_cpf(self):
        for partner in self:
            partner.cnpj_cpf = partner.vat

    @api.depends("vat")
    def _compute_cnpj_cpf_stripped(self):
        for record in self:
            if record.vat:
                record.cnpj_cpf_stripped = "".join(
                    char for char in record.vat if char.isalnum()
                )
            else:
                record.cnpj_cpf_stripped = False

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
