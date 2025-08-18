# Copyright (C) 2009 Gabriel C. Stabel
# Copyright (C) 2009 Renato Lima (Akretion)
# Copyright (C) 2012 Raphaël Valyi (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


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
        names += ["cnpj_cpf_stripped", "legal_name", "l10n_br_ie_code"]
        return names

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

    is_accountant = fields.Boolean(string="Is accountant?")

    crc_code = fields.Char(string="CRC Code", size=18)

    crc_state_id = fields.Many2one(comodel_name="res.country.state", string="CRC State")

    rntrc_code = fields.Char(string="RNTRC Code", size=12)

    cei_code = fields.Char(string="CEI Code", size=12)

    union_entity_code = fields.Char(string="Union Entity code")

    l10n_br_rg_code = fields.Char(string="RG")

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

    def _commercial_sync_to_children(self, fields_to_sync=None):
        """
        Overriden to avoid copying the CNPJ (vat field) to parent partners
        """
        if not self.is_br_partner:
            return super()._commercial_sync_to_children(fields_to_sync)

        commercial_partner = self.commercial_partner_id
        sync_vals = commercial_partner._update_fields_values(
            [field for field in self._commercial_fields() if field != "vat"]
        )
        sync_children = self.child_ids.filtered(lambda c: not c.is_company)
        for child in sync_children:
            child._commercial_sync_to_children(fields_to_sync)
        res = sync_children.write(sync_vals)
        sync_children._compute_commercial_partner()
        return res

    @api.constrains("vat", "l10n_br_ie_code")
    def _check_cnpj_l10n_br_ie_code(self):
        for record in self:
            domain = []

            if not record.vat:
                return

            if self.env.context.get(
                "disable_allow_cnpj_multi_ie"
            ) or self.env.context.get("allow_vat_duplicate"):
                return

            allow_cnpj_multi_ie = (
                record.env["ir.config_parameter"]
                .sudo()
                .get_param("l10n_br_base.allow_cnpj_multi_ie", default=True)
            )

            if record.parent_id:
                domain += [
                    ("id", "not in", record.parent_id.ids),
                    ("parent_id", "not in", record.parent_id.ids),
                ]

            if record.vat:
                domain += [
                    ("vat", "=", record.vat),
                    ("id", "!=", record.id),
                    ("parent_id", "!=", record.id),
                ]
                return

            matches = record.env["res.partner"].search(domain)
            if matches:
                if cnpj_cpf.validar_cnpj(record.vat):
                    if allow_cnpj_multi_ie == "True":
                        for partner in record.env["res.partner"].search(domain):
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
                                vat=self.vat,
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
                duplicate_ie = self.env["res.partner"].search(
                    [
                        ("state_id", "=", l10n_br_ie_code_line.state_id.id),
                        ("l10n_br_ie_code", "=", l10n_br_ie_code_line.l10n_br_ie_code),
                        ("id", "!=", record.id),
                    ]
                )
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
