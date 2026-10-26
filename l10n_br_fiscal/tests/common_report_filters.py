# Copyright (C) 2026-Today - KMEE (<https://kmee.com.br>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tools.safe_eval import safe_eval


class FiscalReportFiltersCase:
    """Checks the standard fiscal filters injected in a search view."""

    def assertFiscalFilters(self, model, present, absent=(), view_id=False):
        arch = self.env[model].get_views([(view_id, "search")])["views"]["search"][
            "arch"
        ]
        filters = {
            node.get("name"): node.get("domain")
            for node in etree.fromstring(arch).iter("filter")
        }
        for name in present:
            self.assertIn(name, filters)
        for name in absent:
            self.assertNotIn(name, filters)
        # every injected domain must be searchable on the model
        for name, domain in filters.items():
            if name.startswith("fiscal_") and domain:
                self.env[model].search_count(safe_eval(domain))
        return filters
