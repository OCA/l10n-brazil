# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import HttpCase, tagged


def _hoot_hash(name):
    """Id of a Hoot suite, the same hash as HOOTCommon of the web module."""
    value = 0
    for char in name:
        value = ((value << 5) - value + ord(char)) & 0xFFFFFFFF
    return f"{value:08x}"


@tagged("post_install", "-at_install")
class TestDdaUiTour(HttpCase):
    def test_inbox_tour(self):
        self.start_tour(
            "/odoo/action-l10n_br_dda.action_dda_debit",
            "l10n_br_dda_inbox_tour",
            login="admin",
        )


@tagged("post_install", "-at_install")
class TestDdaUnitJs(HttpCase):
    def test_unit_js(self):
        self.browser_js(
            "/web/tests?headless&loglevel=2&preset=desktop&timeout=15000"
            f"&id={_hoot_hash('@l10n_br_dda')}",
            "",
            "",
            login="admin",
            timeout=1800,
            success_signal="[HOOT] Test suite succeeded",
            error_checker=lambda message: "[HOOT]" not in message,
        )
