from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..constants.icms import ICMS_TAX_BENEFIT_TYPE


class IcmsBenefit(models.Model):
    _name = "l10n_br_fiscal.icms.benefit"

    code = fields.Char(size=8, required=True)

    description = fields.Text()

    type = fields.Selection(
        selection=ICMS_TAX_BENEFIT_TYPE,
        compute="_compute_type",
    )

    state_id = fields.Many2one(
        comodel_name="res.country.state",
        domain=[("country_id.code", "=", "BR")],
        compute="_compute_state",
        string="State",
    )

    display_name = fields.Char(compute="_compute_display_name", store=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.code))
        return result

    @api.depends("code")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.code}"

    @api.constrains("code")
    def _check_tax_benefit_code(self):
        for record in self:
            if record.code:
                if len(record.code) != 8:
                    raise ValidationError(_("Tax benefit code must be 8 characters!"))

    @api.depends("code")
    def _compute_type(self):
        valid_types = {choice[0] for choice in self._fields["type"].selection}
        for record in self:
            if record.code and len(record.code) >= 4:
                extracted_type = record.code[3]
                if extracted_type in valid_types:
                    record.type = extracted_type
                else:
                    raise UserError(
                        f"Invalid type '{extracted_type}' extracted from code "
                        f"'{record.code}'."
                    )
            else:
                record.type = False

    @api.depends("code")
    def _compute_state(self):
        for record in self:
            record.state_id = (
                self.env["res.country.state"]
                .search(
                    [
                        ("country_id.code", "=", "BR"),
                        ("code", "=", record.code[:2].upper()),
                    ],
                    limit=1,
                )
                .id
                if record.code
                else False
            )
