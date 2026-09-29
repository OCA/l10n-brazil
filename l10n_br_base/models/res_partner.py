# Copyright (C) 2009 Gabriel C. Stabel
# Copyright (C) 2009 Renato Lima (Akretion)
# Copyright (C) 2012 Raphaël Valyi (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base.fiscal import cnpj_cpf

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..tools import check_cnpj_cpf, check_ie


class Partner(models.Model):
    _name = "res.partner"
    _inherit = [_name, "l10n_br_base.party.mixin"]

    @property
    def _rec_names_search(self):
        names = super()._rec_names_search
        # not "names +=": that would extend the parent class attribute in place
        return names + ["cnpj_cpf_stripped", "legal_name", "l10n_br_ie_code"]

    def _inverse_street_data(self):
        """In Brazil the address format is street_name, street_number
        (comma instead of space)"""
        br_partner_ids = self.filtered(lambda line: line._is_br_partner())
        not_br_partner = self - br_partner_ids
        for partner in br_partner_ids:
            street = (
                (partner.street_name or "") + ", " + (partner.street_number or "")
            ).strip()
            if partner.street_number2:
                street = street + " - " + partner.street_number2
            partner.street = street
        return super(Partner, not_br_partner)._inverse_street_data()

    l10n_br_rg_code = fields.Char(string="RG")

    pix_key_ids = fields.One2many(
        string="Pix Keys",
        comodel_name="res.partner.pix",
        inverse_name="partner_id",
        help="Keys for Brazilian instant payment (pix)",
    )

    is_br_partner = fields.Boolean(
        compute="_compute_br_partner",
        help="Is it a Brazilian partner?",
    )

    def copy(self, default=None):
        if self.is_br_partner:
            if default is None:
                default = {}
            if "vat" not in default:
                # CNPJ should be unique:
                default["vat"] = None
        return super().copy(default)

    def _commercial_sync_from_company(self):
        """Overridden to avoid copying the CNPJ (vat field) to child partners.

        Odoo 20.0 renamed ``_commercial_sync_to_children`` into
        ``_commercial_sync_to_descendants`` and routes the values through
        ``_write_commercial_sync``.
        """
        if not self.is_br_partner:
            return super()._commercial_sync_from_company()

        commercial_partner = self.commercial_partner_id
        if commercial_partner != self:
            sync_vals = commercial_partner._get_commercial_values()
            sync_vals.pop("vat", None)
            if sync_vals:
                self._write_commercial_sync(sync_vals)
                self._commercial_sync_to_descendants()
            self._company_dependent_commercial_sync()

    def _commercial_sync_to_descendants(self, fields_to_sync=None):
        """Overridden to avoid copying the CNPJ (vat field) to parent partners."""
        if not self.is_br_partner:
            return super()._commercial_sync_to_descendants(fields_to_sync)

        if fields_to_sync is None:
            fields_to_sync = self._commercial_fields()
        fields_to_sync = [fname for fname in fields_to_sync if fname != "vat"]
        commercial_partner = self.commercial_partner_id
        sync_vals = commercial_partner._convert_fields_to_values(fields_to_sync)
        sync_children = self.child_ids.filtered(lambda c: not c.is_company)
        for child in sync_children:
            child._commercial_sync_to_descendants(fields_to_sync)
        if sync_vals:
            sync_children._write_commercial_sync(sync_vals)

    @api.constrains("vat", "l10n_br_ie_code")
    def _check_cnpj_l10n_br_ie_code(self):
        for record in self:
            if not record.vat:
                continue

            if self.env.context.get(
                "disable_allow_cnpj_multi_ie"
            ) or self.env.context.get("allow_vat_duplicate"):
                continue

            # allow_cnpj_multi_ie is a res.config.settings boolean: the
            # parameter is absent (or stored as "False") when the setting is
            # disabled, so get_bool() reads it correctly (absent -> strict),
            # matching base_setup.show_effect.
            allow_cnpj_multi_ie = (
                record.env["ir.config_parameter"]
                .sudo()
                .get_bool("l10n_br_base.allow_cnpj_multi_ie")
            )

            domain = []
            if record.parent_id:
                domain += [
                    ("id", "not in", record.parent_id.ids),
                    ("parent_id", "not in", record.parent_id.ids),
                ]

            domain += [
                ("vat", "=", record.vat),
                ("id", "!=", record.id),
                ("parent_id", "!=", record.id),
            ]

            matches = record.env["res.partner"].search(domain, limit=1)
            if matches:
                if cnpj_cpf.validar_cnpj(record.vat):
                    if allow_cnpj_multi_ie:
                        for partner in matches:
                            if (
                                partner.l10n_br_ie_code == record.l10n_br_ie_code
                                and record.l10n_br_ie_code
                            ):
                                raise ValidationError(
                                    self.env._(
                                        "There is already a partner %(name)s "
                                        "(ID %(partner_id)s) with this "
                                        "Estadual Inscription %(incr_est)s!",
                                        name=partner.name,
                                        partner_id=partner.id,
                                        incr_est=partner.l10n_br_ie_code,
                                    )
                                )
                    else:
                        raise ValidationError(
                            self.env._(
                                "There is already a partner %(name)s "
                                "(ID %(partner_id)s) with this CNPJ %(vat)s!",
                                name=matches[0].name,
                                partner_id=matches[0].id,
                                vat=record.vat,
                            )
                        )
                elif not record.is_company:
                    raise ValidationError(
                        self.env._(
                            "There is already a partner %(name)s (ID %(partner_id)s) "
                            "with this CPF/RG! %(vat)s",
                            name=matches[0].name,
                            partner_id=matches[0].id,
                            vat=matches[0].vat,
                        )
                    )

    @api.constrains("vat", "country_id")
    def _check_cnpj_cpf(self):
        for record in self:
            check_cnpj_cpf(
                record.env,
                record.vat,
                record.country_id,
            )

    @api.constrains("l10n_br_ie_code", "state_id", "is_company")
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False.
        """
        for record in self:
            if record.is_company:
                check_ie(
                    record.env,
                    record.l10n_br_ie_code,
                    record.state_id,
                    record.country_id,
                )

    @api.constrains("state_tax_number_ids")
    def _check_state_tax_number_ids(self):
        """Checks if field other insc_est is valid,
        this method call others methods because this validation is State wise
        :Return: True or False.
        """
        for record in self:
            for l10n_br_ie_code_line in record.state_tax_number_ids:
                check_ie(
                    record.env,
                    l10n_br_ie_code_line.l10n_br_ie_code,
                    l10n_br_ie_code_line.state_id,
                    record.country_id,
                )

                if l10n_br_ie_code_line.state_id.id == record.state_id.id:
                    raise ValidationError(
                        self.env._(
                            "There can only be one state tax"
                            " number per state for each partner!"
                        )
                    )
                duplicate_ie = self.env["res.partner"].search(
                    [
                        ("state_id", "=", l10n_br_ie_code_line.state_id.id),
                        ("l10n_br_ie_code", "=", l10n_br_ie_code_line.l10n_br_ie_code),
                        ("id", "!=", record.id),
                    ]
                )
                if duplicate_ie:
                    raise ValidationError(
                        self.env._(
                            "State Tax Number already used %(name)s",
                            name=duplicate_ie.name,
                        )
                    )

    @api.model
    def _address_fields(self):
        """Returns the list of address
        fields that are synced from the parent."""
        return super()._address_fields() + ["district"]

    @api.onchange("city_id")
    def _onchange_city_id(self):
        self.city = self.city_id.name

    @api.depends("has_vat", "vat", "commercial_partner_id")
    def _compute_is_company(self):
        """Refine the core heuristic for Brazil.

        Odoo 20.0 dropped the Person/Company switch and computes ``is_company``
        from the commercial entity and a non void ``vat``. In Brazil the CPF
        (individual) and the CNPJ (company) share the same ``vat`` field, so
        every individual holding a CPF would otherwise be flagged as a company.
        """
        cpf_partners = self.filtered(
            lambda partner: cnpj_cpf.validar_cpf(partner.vat or "")
        )
        for partner in cpf_partners:
            partner.is_company = False
        return super(Partner, self - cpf_partners)._compute_is_company()

    def _check_vat(self, validation="error"):
        """Skip the core VAT check when the Brazilian validation is disabled.

        Odoo 20.0 validates the VAT itself in ``base`` (``check_vat_br``
        accepts both the CPF and the CNPJ), so the l10n_br_base setting that
        disables the validation must also bypass the core check.
        """
        if self._l10n_br_disable_vat_validation():
            return
        return super()._check_vat(validation=validation)

    def _is_br_partner(self):
        """Check if is a Brazilian Partner."""
        return bool(
            self.country_id
            and self.country_id == self.env.ref("base.br")
            or self.vat
            and (cnpj_cpf.validar_cnpj(self.vat) or cnpj_cpf.validar_cpf(self.vat))
        )

    def _compute_br_partner(self):
        """Check if is a Brazilian Partner."""
        for record in self:
            record.is_br_partner = record._is_br_partner()
