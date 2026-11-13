# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ServiceType(models.Model):
    """Fiscal Service Type - Tabela de Códigos de Serviço
    [LC 166] Lei Complementar 116 / 2013"""

    _name = "l10n_br_fiscal.service.type"
    _inherit = [
        "l10n_br_fiscal.data.product.abstract",
        "mail.thread",
        "mail.activity.mixin",
    ]
    _description = "Service Type LC 166"

    parent_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.service.type", string="Parent Service Type"
    )

    child_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.service.type",
        inverse_name="parent_id",
        string="Service Type Child",
    )

    internal_type = fields.Selection(
        selection=[("view", "View"), ("normal", "Normal")],
        required=True,
        default="normal",
    )

    product_tmpl_ids = fields.One2many(inverse_name="service_type_id")

    withholding_at_place = fields.Boolean(
        string="Tax Retention at place of provision",
        help="The tax is due at the location of the provider establishment, "
        "except in the cases that this field is true, "
        "where it will be due at the place of provision.",
    )

    withholding_possible = fields.Boolean(string="Subject to withholding tax")

    @api.constrains("code")
    def _check_code_uniq(self):
        # The code is the identity of the record and the base of its xml_id
        # (see _get_xml_id_name), so it must stay unique. A SQL constraint
        # would be silently skipped on a database that already holds
        # duplicated codes (Odoo only logs a warning and never retries),
        # leaving the model unprotected. A Python constraint keeps new
        # duplicates out everywhere and still lets the legacy rows be fixed
        # by hand instead of breaking the module update.
        for record in self.filtered("code"):
            if self.search_count([("code", "=", record.code), ("id", "!=", record.id)]):
                raise ValidationError(_("service_type already exists with this code!"))

    def _get_xml_id_name(self):
        self.ensure_one()
        return f"service_type_{self.code.replace('.', '')}"
