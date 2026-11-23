# Copyright 2025 Engenere.one
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.osv import expression

SEARCH_CONTEXT_KEY = "uom_search_fiscal_code"


class Uom(models.Model):
    _inherit = "uom.uom"

    @api.model
    def _match_by_fiscal_code(self, *codes):
        """Match a unit from one or more fiscal unit codes (the uCom and uTrib of an
        imported document): first by ``code``, then by the aliases of ``uom_alias``,
        so that an abbreviation of the supplier resolves to the unit of the company.
        """
        codes = [code for code in codes if code]
        if not codes:
            return self.browse()
        uom = self.search([("code", "in", codes)], limit=1)
        if not uom:
            uom = self.search([("alias_ids.code", "in", codes)], limit=1)
        return uom

    @api.model
    def _name_search(
        self, name="", args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        if not (self.env.context.get(SEARCH_CONTEXT_KEY) and name):
            return super()._name_search(name, args, operator, limit, name_get_uid)
        # The way a person thinks of a unit: by its fiscal code or by an alias
        domain = [
            "|",
            "|",
            ("code", operator, name),
            ("alias_ids.code", operator, name),
            ("name", operator, name),
        ]
        return self._search(
            expression.AND([domain, args or []]),
            limit=limit,
            access_rights_uid=name_get_uid,
        )
