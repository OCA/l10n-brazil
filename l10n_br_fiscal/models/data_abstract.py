# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import json

from erpbrasil.base import misc
from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import AccessError
from odoo.osv import expression

from .. import tools


class DataAbstract(models.AbstractModel):
    """
    Abstract base model for fiscal master data in Brazilian localization.

    This model provides common structure and functionality for fiscal
    data entities (NCM, CFOP, CST, etc.). It includes:
    - Standard fields: `code`, `name`, `active`, and a computed
      `code_unmasked` (for searching codes without punctuation).
    - Default ordering by `code`.
    - Enhanced search: Modifies search views and `_name_search`
      to allow searching by `code`, `code_unmasked`, and `name`
      simultaneously.
    - Standardized display name format in `name_get`
      (`<code> - <name>`).
    - Permission control for archiving/unarchanging, restricted
      to users in 'l10n_br_fiscal.group_manager' group.
    """

    _name = "l10n_br_fiscal.data.abstract"
    _description = "Fiscal Data Abstract"
    _order = "code"

    code = fields.Char(required=True, index=True)

    name = fields.Text(required=True, index=True)

    code_unmasked = fields.Char(
        string="Unmasked Code", compute="_compute_code_unmasked", store=True, index=True
    )

    active = fields.Boolean(default=True)

    date_start = fields.Date(string="Start Date")

    date_end = fields.Date(string="End Date")

    _sql_constraints = [
        (
            "dt_end_greater_dt_start",
            "check (date_end >= date_start)",
            "The end date must be greater than or equal to the start date.",
        )
    ]

    def action_archive(self):
        if not self.env.user.has_group("l10n_br_fiscal.group_manager"):
            raise AccessError(_("You don't have permission to archive records."))
        return super().action_archive()

    def action_unarchive(self):
        if not self.env.user.has_group("l10n_br_fiscal.group_manager"):
            raise AccessError(_("You don't have permission to unarchive records."))
        return super().action_unarchive()

    @api.model
    def _get_invalid_records(self):
        """Return active records whose validity window (date_start/date_end)
        does not include today."""
        today = fields.Date.context_today(self)
        active_records = self.search([("active", "=", True)])
        valid_records = self.search(
            [("active", "=", True)] + tools.date_validity_domain(today)
        )
        return active_records - valid_records

    @api.model
    def _expire_invalid_records(self):
        """Deactivate records that fell outside their date validity window."""
        invalid_records = self._get_invalid_records()
        if invalid_records:
            invalid_records.write({"active": False})

    @api.model
    def _cron_expire_fiscal_parametrization(self):
        """Daily cron entry point: deactivate fiscal master data outside
        their validity window, and mark expired fiscal operation lines and
        tax definitions.

        Iterates every concrete model that inherits from this abstract
        model (NCM, NBS, CFOP, CST, CEST, NBM, ...), including through the
        intermediate `data.product.abstract` / `data.ncm.nbs.abstract`
        abstractions.
        """
        abstract_class = self.pool["l10n_br_fiscal.data.abstract"]
        for model_name, model_class in self.pool.models.items():
            if model_class._abstract or model_class._transient:
                continue
            if not issubclass(model_class, abstract_class):
                continue
            self.env[model_name]._expire_invalid_records()

        self.env["l10n_br_fiscal.operation.line"]._expire_invalid_lines()
        self.env["l10n_br_fiscal.tax.definition"]._expire_invalid_definitions()

    @api.depends("code")
    def _compute_code_unmasked(self):
        for r in self:
            # TODO mask code and unmasck
            r.code_unmasked = misc.punctuation_rm(r.code)

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        """
        Modify search view architecture to enhance 'code' field filtering.

        Intercept the search view definition, altering `filter_domain`
        for the 'code' field. This lets users search by raw 'code',
        'code_unmasked' (code without punctuation), or 'name' of the
        record when typing into the 'code' filter in the search panel.
        """

        model_view = super().fields_view_get(view_id, view_type, toolbar, submenu)

        if view_type == "search":
            doc = etree.XML(model_view["arch"])
            for node in doc.xpath("//field[@name='code']"):
                modifiers = json.loads(node.get("modifiers", "{}"))
                modifiers["filter_domain"] = (
                    "['|', '|', ('code', 'ilike', self), "
                    "('code_unmasked', 'ilike', self + '%'),"
                    "('name', 'ilike', self + '%')]"
                )
                node.set("modifiers", json.dumps(modifiers))
            model_view["arch"] = etree.tostring(doc)

        return model_view

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        if operator == "ilike" and not (name or "").strip():
            domain = []
        elif operator in ("ilike", "like", "=", "=like", "=ilike"):
            domain = expression.AND(
                [
                    args or [],
                    [
                        "|",
                        "|",
                        ("name", operator, name),
                        ("code", operator, name),
                        ("code_unmasked", "ilike", name + "%"),
                    ],
                ]
            )
            return self._search(
                expression.AND([domain, args]),
                limit=limit,
                access_rights_uid=name_get_uid,
            )

        return super()._name_search(
            name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid
        )

    def name_get(self):
        def truncate_name(name):
            if len(name) > 60:
                name = f"{name[:60]}..."
            return name

        if self._context.get("show_code_only"):
            return [(r.id, f"{r.code}") for r in self]

        return [(r.id, f"{r.code} - {truncate_name(r.name)}") for r in self]
