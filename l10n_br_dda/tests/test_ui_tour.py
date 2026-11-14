# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import HttpCase, tagged


def _qunit_error_checker(message):
    """Keep running the suite when one QUnit test fails (same as the web suite)."""
    if "tests failed." in message:
        return True
    if "QUnit test failed:" in message:
        return False
    return True


@tagged("post_install", "-at_install")
class TestDdaUiTour(HttpCase):
    def test_inbox_tour(self):
        self.start_tour(
            "/web#action=l10n_br_dda.action_dda_debit",
            "l10n_br_dda_inbox_tour",
            login="admin",
        )


@tagged("post_install", "-at_install")
class TestDdaQunit(HttpCase):
    def test_qunit(self):
        self.browser_js(
            "/web/tests?mod=web&filter=l10n_br_dda",
            "",
            "",
            login="admin",
            timeout=1800,
            error_checker=_qunit_error_checker,
        )
