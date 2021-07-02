# Copyright (C) 2009 Gabriel C. Stabel
# Copyright (C) 2009 Renato Lima (Akretion)
# Copyright (C) 2012 Raphaël Valyi (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base.fiscal import cnpj_cpf, ie
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class Partner(models.Model):
    _name = "res.partner"
    _inherit = [_name, "l10n_br_base.party.mixin"]

    vat = fields.Char(related="cnpj_cpf")

    is_accountant = fields.Boolean(string="Is accountant?")

    crc_code = fields.Char(string="CRC Code", size=18)

    crc_state_id = fields.Many2one(comodel_name="res.country.state", string="CRC State")

    rntrc_code = fields.Char(string="RNTRC Code", size=12)

    cei_code = fields.Char(string="CEI Code", size=12)

    union_entity_code = fields.Char(string="Union Entity code")

    @api.constrains("cnpj_cpf", "inscr_est")
    def _check_cnpj_inscr_est(self):
        for record in self:
            domain = []

            # permite cnpj vazio
            if not record.cnpj_cpf:
                return

            if self.env.context.get("disable_allow_cnpj_multi_ie"):
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

            domain += [("cnpj_cpf", "=", record.cnpj_cpf), ("id", "!=", record.id)]

            # se encontrar CNPJ iguais
            if record.env["res.partner"].search(domain):
                if cnpj_cpf.validar_cnpj(record.cnpj_cpf):
                    if allow_cnpj_multi_ie == "True":
                        for partner in record.env["res.partner"].search(domain):
                            if (
                                partner.inscr_est == record.inscr_est
                                and not record.inscr_est
                            ):
                                raise ValidationError(
                                    _(
                                        "There is already a partner record with this "
                                        "Estadual Inscription !"
                                    )
                                )
                    else:
                        raise ValidationError(
                            _("There is already a partner record with this CNPJ !")
                        )
                else:
                    raise ValidationError(
                        _("There is already a partner record with this CPF/RG!")
                    )

    @api.constrains("cnpj_cpf", "country_id")
    def _check_cnpj_cpf(self):
        result = True
        for record in self:

            disable_cnpj_ie_validation = record.env[
                "ir.config_parameter"
            ].sudo().get_param(
                "l10n_br_base.disable_cpf_cnpj_validation", default=False
            ) or self.env.context.get(
                "disable_cpf_cnpj_validation"
            )
            if not disable_cnpj_ie_validation:
                if record.country_id:
                    country_code = record.country_id.code
                    if country_code:
                        if record.cnpj_cpf and country_code.upper() == "BR":
                            if record.is_company:
                                if not cnpj_cpf.validar(record.cnpj_cpf):
                                    result = False
                                    document = "CNPJ"
                            elif not cnpj_cpf.validar(record.cnpj_cpf):
                                result = False
                                document = "CPF"
                if not result:
                    raise ValidationError(_("{} Invalid!").format(document))

    @api.constrains("inscr_est", "state_id")
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False.

        :Parameters:
        """
        for record in self:
            result = True

            disable_ie_validation = record.env["ir.config_parameter"].sudo().get_param(
                "l10n_br_base.disable_ie_validation", default=False
            ) or self.env.context.get("disable_ie_validation")
            if not disable_ie_validation:
                if record.inscr_est == "ISENTO":
                    return
                if record.inscr_est and record.is_company and record.state_id:
                    state_code = record.state_id.code or ""
                    uf = state_code.lower()
                    result = ie.validar(uf, record.inscr_est)
                if not result:
                    raise ValidationError(_("Estadual Inscription Invalid !"))

    @api.constrains("state_tax_number_ids")
    def _check_state_tax_number_ids(self):
        """Checks if field other insc_est is valid,
        this method call others methods because this validation is State wise
        :Return: True or False.
        """
        for record in self:
            for inscr_est_line in record.state_tax_number_ids:
                state_code = inscr_est_line.state_id.code or ""
                uf = state_code.lower()
                valid_ie = ie.validar(uf, inscr_est_line.inscr_est)
                if not valid_ie:
                    raise ValidationError(_("Invalid State Tax Number!"))
                if inscr_est_line.state_id.id == record.state_id.id:
                    raise ValidationError(
                        _(
                            "There can only be one state tax"
                            " number per state for each partner!"
                        )
                    )
                duplicate_ie = record.search(
                    [
                        ("state_id", "=", inscr_est_line.state_id.id),
                        ("inscr_est", "=", inscr_est_line.inscr_est),
                    ]
                )
                if duplicate_ie:
                    raise ValidationError(
                        _("State Tax Number already used" " %s" % duplicate_ie.name)
                    )

    @api.model
    def _address_fields(self):
        """Returns the list of address
        fields that are synced from the parent."""
        return super()._address_fields() + ["district"]

    def _get_street_fields(self):
        """Returns the fields that can be used in a street format.
        Overwrite this function if you want to add your own fields."""
        return super()._get_street_fields() + ["street"]

    @api.onchange("city_id")
    def _onchange_city_id(self):
        self.city = self.city_id.name

    # overriden nearly as a copy from the base_address_extended module
    # but modified in the end because of https://github.com/odoo/odoo/pull/71630
    def _set_street(self):
        """Updates the street field.
        Writes the `street` field on the partners when one of the sub-fields in
        STREET_FIELDS has been touched"""
        street_fields = self.get_street_fields()
        for partner in self:
            street_format = (
                partner.country_id.street_format
                or "%(street_number)s/%(street_number2)s %(street_name)s"
            )
            previous_field = None
            previous_pos = 0
            street_value = ""
            separator = ""
            # iter on fields in street_format, detected as '%(<field_name>)s'
            for re_match in re.finditer(r"%\(\w+\)s", street_format):
                # [2:-2] is used to remove the extra chars '%(' and ')s'
                field_name = re_match.group()[2:-2]
                field_pos = re_match.start()
                if field_name not in street_fields:
                    raise UserError(
                        _("Unrecognized field %s in street format.") % field_name
                    )
                if not previous_field:
                    # first iteration: add heading chars in street_format
                    if partner[field_name]:
                        street_value += street_format[0:field_pos] + partner[field_name]
                else:
                    # get the substring between 2 fields, to be used as separator
                    separator = street_format[previous_pos:field_pos]
                    if street_value and partner[field_name]:
                        street_value += separator
                    if partner[field_name]:
                        street_value += partner[field_name]
                previous_field = field_name
                previous_pos = re_match.end()

            # add trailing chars in street_format
            street_value += street_format[previous_pos:]
            # see https://github.com/odoo/odoo/pull/71630
            if partner.street != street_value:
                partner.street = street_value
