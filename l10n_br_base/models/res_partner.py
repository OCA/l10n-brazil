# Copyright (C) 2009 Gabriel C. Stabel
# Copyright (C) 2009 Renato Lima (Akretion)
# Copyright (C) 2012 Raphaël Valyi (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from collections import defaultdict

from erpbrasil.base.fiscal import cnpj_cpf

from odoo import _, api, fields, models
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

    l10n_br_rg_code = fields.Char(string="RG", unaccent=False)

    pix_key_ids = fields.One2many(
        string="Pix Keys",
        comodel_name="res.partner.pix",
        inverse_name="partner_id",
        help="Keys for Brazilian instant payment (pix)",
    )

    show_l10n_br = fields.Boolean(
        compute="_compute_show_l10n_br",
        help="Should display Brazilian localization fields?",
    )

    is_br_partner = fields.Boolean(
        compute="_compute_br_partner",
        help="Is it a Brazilian partner?",
    )

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        if self.is_br_partner:
            if default is None:
                default = {}
            if "vat" not in default:
                # CNPJ should be unique:
                default["vat"] = None
        return super().copy(default)

    def _commercial_sync_from_company(self):
        """
        Overriden to avoid copying the CNPJ (vat field) to children companies
        """
        if not self.is_br_partner:
            return super()._commercial_sync_from_company()

        commercial_partner = self.commercial_partner_id
        if commercial_partner != self:
            sync_vals = commercial_partner._update_fields_values(
                [field for field in self._commercial_fields() if field != "vat"]
            )
            self.write(sync_vals)
            self._commercial_sync_to_children()

    def _commercial_sync_to_children(self):
        """
        Overriden to avoid copying the CNPJ (vat field) to parent partners
        """
        if not self.is_br_partner:
            return super()._commercial_sync_to_children()

        commercial_partner = self.commercial_partner_id
        sync_vals = commercial_partner._update_fields_values(
            [field for field in self._commercial_fields() if field != "vat"]
        )
        sync_children = self.child_ids.filtered(lambda c: not c.is_company)
        for child in sync_children:
            child._commercial_sync_to_children()
        res = sync_children.write(sync_vals)
        sync_children._compute_commercial_partner()
        return res

    @api.constrains("vat", "l10n_br_ie_code")
    def _check_cnpj_l10n_br_ie_code(self):
        if self.env.context.get("disable_allow_cnpj_multi_ie") or self.env.context.get(
            "allow_vat_duplicate"
        ):
            return

        # allow_cnpj_multi_ie is a res.config.settings boolean: it is stored
        # as "True" when enabled and removed entirely when disabled
        # (set_param deletes on a False bool), so a plain bool() reads it
        # correctly (absent -> strict), matching base_setup.show_effect.
        # It is the same for every record, so it is read once.
        allow_cnpj_multi_ie = bool(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_br_base.allow_cnpj_multi_ie")
        )

        # Compare by the normalized CNPJ/CPF (cnpj_cpf_stripped, without mask)
        # so the same number typed with a different mask is still detected as
        # a duplicate: `vat` is only normalized when written through the
        # `cnpj_cpf` alias, so a direct `vat` write could store a different
        # mask and slip past a raw `vat` comparison.
        # Skip an empty normalized document (e.g. `vat = "/"`, which `base`
        # documents as "not subject to tax"): it would otherwise match every
        # other partner with an empty document.
        # NOTE: 18.0 stores `vat` unformatted (OCA/l10n-brazil#4671) and
        # compares by `vat` directly.
        records = self.filtered(lambda r: r.vat and r.cnpj_cpf_stripped)

        # Fetch the candidates of every record without a parent in one query
        # instead of one search() per record. Records with a parent keep their
        # own search: their domain also excludes the parent and its children.
        candidates_by_stripped = defaultdict(list)
        stripped_values = list(
            set(records.filtered(lambda r: not r.parent_id).mapped("cnpj_cpf_stripped"))
        )
        if stripped_values:
            for candidate in self.env["res.partner"].search(
                [("cnpj_cpf_stripped", "in", stripped_values)]
            ):
                candidates_by_stripped[candidate.cnpj_cpf_stripped].append(candidate)

        for record in records:
            if record.parent_id:
                matches = record.env["res.partner"].search(
                    [
                        ("id", "not in", record.parent_id.ids),
                        ("parent_id", "not in", record.parent_id.ids),
                        ("cnpj_cpf_stripped", "=", record.cnpj_cpf_stripped),
                        ("id", "!=", record.id),
                        ("parent_id", "!=", record.id),
                    ]
                )
            else:
                # Same filter as the domain above, in memory and in the search
                # order. ("parent_id", "!=", id) keeps the rows without parent.
                matches = record.env["res.partner"].browse(
                    [
                        candidate.id
                        for candidate in candidates_by_stripped[
                            record.cnpj_cpf_stripped
                        ]
                        if candidate.id != record.id
                        and candidate.parent_id.id != record.id
                    ]
                )

            if matches:
                if cnpj_cpf.validar_cnpj(record.vat):
                    if allow_cnpj_multi_ie:
                        for partner in matches:
                            if (
                                partner.l10n_br_ie_code == record.l10n_br_ie_code
                                and record.l10n_br_ie_code
                            ):
                                raise ValidationError(
                                    _(
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
                            _(
                                "There is already a partner %(name)s "
                                "(ID %(partner_id)s) with this CNPJ %(vat)s!",
                                name=matches[0].name,
                                partner_id=matches[0].id,
                                vat=record.vat,
                            )
                        )
                elif not record.is_company:
                    raise ValidationError(
                        _(
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
        # Fetch the candidates of every line in one query, grouped by
        # (state_id, l10n_br_ie_code), instead of one search() per line.
        # Both fields are required on the line, so no NULL to match.
        all_lines = self.mapped("state_tax_number_ids")
        duplicates_by_key = {}
        if all_lines:
            state_ids = all_lines.mapped("state_id").ids
            ie_codes = list(
                {
                    code
                    for code in all_lines.mapped("l10n_br_ie_code")
                    if code is not False
                }
            )
            if state_ids and ie_codes:
                for partner in self.env["res.partner"].search(
                    [
                        ("state_id", "in", state_ids),
                        ("l10n_br_ie_code", "in", ie_codes),
                    ]
                ):
                    key = (partner.state_id.id, partner.l10n_br_ie_code)
                    duplicates_by_key.setdefault(key, self.env["res.partner"])
                    duplicates_by_key[key] |= partner

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
                        _(
                            "There can only be one state tax"
                            " number per state for each partner!"
                        )
                    )
                # Same filter as the former per-line search (state + IE code,
                # excluding the record itself), in memory and in search order.
                key = (
                    l10n_br_ie_code_line.state_id.id,
                    l10n_br_ie_code_line.l10n_br_ie_code,
                )
                duplicate_ie = duplicates_by_key.get(
                    key, self.env["res.partner"]
                ).filtered(lambda p, rid=record.id: p.id != rid)
                if duplicate_ie:
                    raise ValidationError(
                        _("State Tax Number already used {}").format(duplicate_ie.name)
                    )

    @api.model
    def _address_fields(self):
        """Returns the list of address
        fields that are synced from the parent."""
        return super()._address_fields() + ["district"]

    @api.onchange("city_id")
    def _onchange_city_id(self):
        self.city = self.city_id.name

    def _compute_show_l10n_br(self):
        """
        Defines when Brazilian localization fields should be displayed.
        """
        for rec in self:
            if rec.company_id and rec.company_id.country_id != self.env.ref("base.br"):
                rec.show_l10n_br = False
            else:
                rec.show_l10n_br = True

    def create_company(self):
        self.ensure_one()
        res = super(
            Partner, self.with_context(allow_vat_duplicate=True)
        ).create_company()
        if res and self.is_br_partner:
            parent = self.parent_id
            parent.legal_name = parent.name
            parent.l10n_br_ie_code = self.l10n_br_ie_code
            parent.l10n_br_im_code = self.l10n_br_im_code
        return res

    def _is_br_partner(self):
        """Check if is a Brazilian Partner."""
        if (
            self.country_id
            and self.country_id == self.env.ref("base.br")
            or self.vat
            and (cnpj_cpf.validar_cnpj(self.vat) or cnpj_cpf.validar_cpf(self.vat))
        ):
            return True
        return False

    def _compute_br_partner(self):
        """Check if is a Brazilian Partner."""
        for record in self:
            record.is_br_partner = record._is_br_partner()
